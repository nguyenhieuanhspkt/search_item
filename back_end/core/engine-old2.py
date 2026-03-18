import os
import numpy as np
import re
import torch
import json
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from whoosh.index import open_dir, exists_in, create_in
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path=None, index_dir=None):
        # 1. Xác định các đường dẫn
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        
        # Load Categories từ JSON
        self.cat_path = os.path.join(current_dir, "categories.json")
        self.category_data = self.load_categories()
        self.category_names = list(self.category_data.keys())
        self.cat_vectors = None

        # Cấu hình Model BGE-M3 (Ưu tiên local)
        local_bge_path = os.path.join(backend_dir, "AI_models", "BGE")
        final_model = local_bge_path if os.path.exists(local_bge_path) else 'keepitreal/vietnamese-sbert'
        self.index_dir = index_dir or os.path.join(backend_dir, "vattu_index")
        
        # Tối ưu hóa CPU
        torch.set_num_threads(4)
        
        try:
            print(f"--- Đang nạp Model từ: {final_model} ---")
            self.bi_model = SentenceTransformer(final_model, device='cpu')
            self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')
            
            # Gán biến đường dẫn để main.py không bị lỗi attribute
            self.current_model_name_or_path = final_model
            
            # Tính toán sẵn Vector cho các tên Chủng loại
            if self.category_names:
                self.cat_vectors = self.bi_model.encode(self.category_names, convert_to_tensor=True)
            
            print(f"--- ✅ AI Engine Ready (Mode: {self.current_model_name_or_path}) ---")
        except Exception as e:
            self.current_model_name_or_path = "Error"
            print(f"--- ❌ Lỗi khởi tạo Engine: {str(e)} ---")

    def load_categories(self):
        """Đọc danh mục từ file JSON"""
        if os.path.exists(self.cat_path):
            try:
                with open(self.cat_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def predict_category(self, text):
        """Dự đoán chủng loại kết hợp Keyword & AI Semantic"""
        text_low = text.lower()
        # Vòng 1: Keyword match
        for cat, keywords in self.category_data.items():
            if any(kw in text_low for kw in keywords):
                return cat
        
        # Vòng 2: AI suy luận
        if self.cat_vectors is not None:
            text_vec = self.bi_model.encode(text, convert_to_tensor=True)
            cos_sims = util.cos_sim(text_vec, self.cat_vectors)[0]
            best_idx = cos_sims.argmax().item()
            if cos_sims[best_idx] > 0.4:
                    return self.category_names[best_idx]
        return "Vật tư khác"

    def clean_text(self, text):
        """Làm sạch query nhưng giữ lại ký tự kỹ thuật quan trọng"""
        if not text: return ""
        text = re.sub(r'[!"#$%&\'()*+,\-/:;<=>?@[\\\]^_`{|}~]', ' ', text)
        words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
        return " ".join(words)

    def extract_tech_specs(self, text):
        """Trích xuất thông số (Số + Đơn vị) - Thừa kế từ bản ổn định"""
        pattern = r'(\d+[\.\,]*\d*\s*(?:kw|v|a|dn|hp|mm|m|kg|inch|phi|ø|\"|x))'
        specs = re.findall(pattern, text.lower())
        return specs

    def extract_important_codes(self, text):
        """Trích xuất mã hiệu kỹ thuật (SA240, A36...)"""
        pattern = r'([a-zA-Z]+\d+\w*|\d+[a-zA-Z]+\w*)'
        return re.findall(pattern, text.upper())

    def build_and_save_index(self, excel_path, index_dir=None):
        target_dir = index_dir or self.index_dir
        try:
            print(f"--- Bắt đầu xây dựng Index từ: {excel_path} ---")
            df = pd.read_excel(excel_path)
            if not os.path.exists(target_dir): os.makedirs(target_dir)

            schema = Schema(
                ma_vattu=ID(stored=True),
                ten_vattu=TEXT(stored=True),
                thong_so=TEXT(stored=True),
                hang_sx=TEXT(stored=True),
                chung_loai=TEXT(stored=True), # Thêm trường chủng loại vào Index
                dvt=STORED,
                all_text=TEXT(stored=True)
            )

            ix = create_in(target_dir, schema)
            writer = ix.writer()
            for _, row in df.iterrows():
                ten = str(row.get('Tên vật tư', '')).strip()
                ts = str(row.get('Thông số kỹ thuật', '')).strip()
                hang = str(row.get('Hãng sản xuất', '')).strip()
                
                # AI tự gán chủng loại
                cat = self.predict_category(f"{ten} {ts}")
                
                all_val = f"{ten} {ts} {hang}".strip()
                writer.add_document(
                    ma_vattu=str(row.get('Mã vật tư', '')),
                    ten_vattu=ten,
                    thong_so=ts,
                    hang_sx=hang,
                    chung_loai=cat,
                    dvt=str(row.get('ĐVT', 'N/A')),
                    all_text=all_val
                )
            writer.commit()
            print(f"--- ✅ Build Index thành công ---")
            return True
        except Exception as e:
            print(f"--- ❌ Lỗi Build Index: {str(e)} ---")
            return False

    def search(self, query_str, top_k=15, query_vec=None):
        if not exists_in(self.index_dir): return []
        
        ix = open_dir(self.index_dir)
        clean_query = self.clean_text(query_str)
        q_low = query_str.lower()
        
        # --- BƯỚC 1: WHOOSH LỌC NHANH (TẦNG 1) ---
        candidates = []
        with ix.searcher() as searcher:
            og = OrGroup.factory(0.5)
            parser = MultifieldParser(["ten_vattu", "thong_so", "all_text"], ix.schema, group=og)
            query = parser.parse(clean_query)
            results = searcher.search(query, limit=60)
            for hit in results:
                candidates.append({
                    "ma": hit.get('ma_vattu', ''),
                    "ten": hit.get('ten_vattu', ''),
                    "ts": hit.get('thong_so', ''),
                    "hang": hit.get('hang_sx', ''),
                    "chung_loai": hit.get('chung_loai', 'N/A'),
                    "dvt": hit.get('dvt', 'N/A'),
                    "all_text": hit.get('all_text', ''),
                    "w_score": hit.score
                })
        
        if not candidates: return []

        # --- BƯỚC 2: RERANKING VỚI CROSS-ENCODER (TẦNG 2) ---
        top_n = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_n]
        cross_scores = self.cross_model.predict(pairs, batch_size=16)

        # --- BƯỚC 3: BI-ENCODER & CHỈNH ĐIỂM NGHIÊM NGẶT (TẦNG 3) ---
        if query_vec is None:
            query_vec = self.bi_model.encode(query_str, convert_to_tensor=True)
        
        all_docs_text = [c['all_text'] for c in top_n]
        doc_vectors = self.bi_model.encode(all_docs_text, convert_to_tensor=True, batch_size=16)
        cos_scores = util.cos_sim(query_vec, doc_vectors)[0]
        
        # Trích xuất dữ liệu để so khớp cứng
        query_specs = self.extract_tech_specs(query_str) # Các số kèm đơn vị (650mm, 20kw...)
        q_codes = self.extract_important_codes(query_str) # Các mã hiệu (SA240, 310S...)
        # Trích xuất TẤT CẢ con số từ 2 chữ số trở lên (để bắt kích thước 200, 650, 2...)
        q_numbers = re.findall(r'\d{2,}', query_str) 

        for i, c in enumerate(top_n):
            # Điểm từ các Model AI (Bản chất là Semantic - Ngữ nghĩa)
            s_cross = 1 / (1 + np.exp(-cross_scores[i]))
            s_bi = float(cos_scores[i])
            
            bonus = 0
            penalty = 0
            doc_text_low = c['all_text'].lower()
            doc_text_up = c['all_text'].upper()

            # 1. Thưởng điểm nếu khớp mã hiệu kỹ thuật (SA240, 310S...)
            for code in q_codes:
                if len(code) > 2 and code in doc_text_up:
                    bonus += 0.15

            # 2. Thưởng điểm nếu khớp thông số kèm đơn vị (650mm, t3...)
            for spec in query_specs:
                if spec in doc_text_low:
                    bonus += 0.10

            # 3. LOGIC QUAN TRỌNG: SO KHỚP SỐ ĐO (Tránh lỗi 100% ảo)
            if q_numbers:
                match_count = 0
                for num in q_numbers:
                    if num in doc_text_low:
                        match_count += 1
                
                # Tính tỷ lệ khớp số
                match_ratio = match_count / len(q_numbers)
                
                # Thưởng nếu khớp số đo
                bonus += (match_ratio * 0.2) 

                # PHẠT NẶNG: Nếu sai lệch số đo quá nhiều (ví dụ query 200 mà ERP là 60)
                if match_ratio == 0:
                    penalty += 0.35 # Trừ thẳng 35% điểm nếu không khớp số nào
                elif match_ratio < 0.5:
                    penalty += 0.15 # Trừ 15% nếu lệch hơn phân nửa số đo

            # 4. Hình phạt logic nghiệp vụ (Penalty từ bản ổn định)
            if "sealant" in q_low and "van" in doc_text_low: penalty += 0.4
            if "hcl" in q_low and "naoh" in doc_text_low: penalty += 0.6

            # 5. TỔNG HỢP ĐIỂM CUỐI CÙNG
            w_norm = min(c['w_score'] / 50, 1.0)
            
            # Công thức trọng số mới:
            # 40% Cross + 30% Bi + 10% Whoosh + Bonus - Penalty
            final_score = (s_cross * 0.4) + (s_bi * 0.3) + (w_norm * 0.1) + bonus - penalty
            
            # Ép điểm về dải 0 - 1
            c['final_score'] = float(max(min(final_score, 1.0), 0.0))

        # Sắp xếp lại theo điểm mới sau khi đã áp Penalty
        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        for item in top_n: item.pop('all_text', None)
        return top_n[:top_k]

    def search_batch(self, queries, top_k=1):
        if not queries: return []
        query_embs = self.bi_model.encode(queries, convert_to_tensor=True, batch_size=32)
        all_results = []
        for i, q_str in enumerate(queries):
            res = self.search(q_str, top_k=top_k, query_vec=query_embs[i])
            all_results.append(res)
        return all_results