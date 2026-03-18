import os
import numpy as np
import re
import torch
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from whoosh.index import open_dir, exists_in, create_in
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path=None, index_dir=None):
        # 1. Tự động xác định các đường dẫn gốc
        current_dir = os.path.dirname(os.path.abspath(__file__)) # Thư mục core
        backend_dir = os.path.dirname(current_dir)               # Thư mục backend
        
        # Đường dẫn ưu tiên số 1: Folder BGE nằm trong project
        local_bge_path = os.path.join(backend_dir, "AI_models", "BGE")
        # Model dự phòng: Vietnamese-SBERT (tải từ HuggingFace nếu local không có)
        fallback_model = 'keepitreal/vietnamese-sbert'

        # 2. LOGIC CHỌN MODEL (FALLBACK)
        if model_path and os.path.exists(model_path):
            # Nếu main.py truyền đường dẫn cụ thể và nó tồn tại
            final_model = model_path
        elif os.path.exists(local_bge_path) and any(os.scandir(local_bge_path)):
            # Nếu tìm thấy folder BGE trong AI_models và không rỗng
            final_model = local_bge_path
            print(f"--- 🚀 Ưu tiên: Sử dụng model BGE-M3 (Local) ---")
        else:
            # Trường hợp cuối cùng: Dùng Vietnamese-SBERT
            final_model = fallback_model
            print(f"--- ⚠️ Warning: Không tìm thấy BGE, sử dụng dự phòng: Vietnamese-SBERT ---")

        # 3. Cấu hình Index Dir
        if index_dir is None:
            index_dir = os.path.join(backend_dir, "vattu_index")
        self.index_dir = index_dir

        # Tối ưu hóa CPU cho con i5 của bạn (Sử dụng 4 nhân)
        torch.set_num_threads(4)
        
        # 4. KHỞI TẠO MODEL
        try:
            print(f"--- Đang nạp Model từ: {final_model} ---")
            # Nạp Bi-Encoder (BGE hoặc SBERT tùy vào logic trên)
            self.bi_model = SentenceTransformer(final_model, device='cpu')
            
            # Nạp Cross-Encoder (Reranker)
            self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')
            
            print(f"--- ✅ Hệ thống Engine đã sẵn sàng với Index tại: {self.index_dir} ---")
        except Exception as e:
            print(f"--- ❌ Lỗi nghiêm trọng khi nạp Model: {str(e)} ---")
            # Bạn có thể raise lỗi để dừng server nếu model không nạp được
        # LOGIC CHỌN MODEL (FALLBACK)
        if model_path and os.path.exists(model_path):
            final_model = model_path
        elif os.path.exists(local_bge_path) and any(os.scandir(local_bge_path)):
            final_model = local_bge_path
        else:
            final_model = fallback_model

        # LƯU LẠI ĐƯỜNG DẪN THỰC TẾ VÀO BIẾN CỦA CLASS
        self.current_model_name_or_path = final_model

    def clean_text(self, text):
        """Làm sạch query nhưng giữ lại các ký tự kỹ thuật quan trọng"""
        if not text: return ""
        text = re.sub(r'[!"#$%&\'()*+,\-/:;<=>?@[\\\]^_`{|}~]', ' ', text)
        words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
        return " ".join(words)

    def extract_tech_specs(self, text):
        """Trích xuất các thông số kỹ thuật (Số + Đơn vị) để thưởng điểm"""
        pattern = r'(\d+[\.\,]*\d*\s*(?:kw|v|a|dn|hp|mm|m|kg|inch|phi|ø|\"|x))'
        specs = re.findall(pattern, text.lower())
        return specs

    def build_and_save_index(self, excel_path, index_dir=None):
        """
        Đọc Excel và tạo file Index vào thư mục vattu_index
        """
        target_dir = index_dir or self.index_dir
        try:
            print(f"--- Bắt đầu xây dựng Index từ file: {excel_path} ---")
            df = pd.read_excel(excel_path)
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # Định nghĩa Schema cho Whoosh
            schema = Schema(
                ma_vattu=ID(stored=True),
                ten_vattu=TEXT(stored=True),
                thong_so=TEXT(stored=True),
                hang_sx=TEXT(stored=True),
                dvt=STORED,
                all_text=TEXT(stored=True)
            )

            # Tạo Index mới (Ghi đè nếu đã có)
            ix = create_in(target_dir, schema)
            writer = ix.writer()

            for _, row in df.iterrows():
                # Kết hợp dữ liệu để AI dễ tìm kiếm hơn
                ten = str(row.get('Tên vật tư', '')).strip()
                ts = str(row.get('Thông số kỹ thuật', '')).strip()
                hang = str(row.get('Hãng sản xuất', '')).strip()
                
                all_val = f"{ten} {ts} {hang}".strip()
                
                writer.add_document(
                    ma_vattu=str(row.get('Mã vật tư', '')),
                    ten_vattu=ten,
                    thong_so=ts,
                    hang_sx=hang,
                    dvt=str(row.get('ĐVT', 'N/A')),
                    all_text=all_val
                )
            
            writer.commit() # CHỐT HẠ: Lưu xuống ổ đĩa
            print(f"--- ✅ Đã lưu Index thành công ({len(df)} dòng) vào {target_dir} ---")
            return True
        except Exception as e:
            print(f"--- ❌ Lỗi Build Index: {str(e)} ---")
            return False

    def search(self, query_str, top_k=15, query_vec=None):
        """Tìm kiếm lai ghép (Hybrid Search)"""
        if not exists_in(self.index_dir):
            print(f"Lỗi: Folder index {self.index_dir} chưa có dữ liệu.")
            return []
        
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
                    "dvt": hit.get('dvt', 'N/A'),
                    "all_text": hit.get('all_text', ''),
                    "w_score": hit.score
                })
        
        if not candidates: return []

        # --- BƯỚC 2: CROSS-ENCODER RERANKING (TẦNG 2) ---
        top_n = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_n]
        cross_scores = self.cross_model.predict(pairs, batch_size=16)

        # --- BƯỚC 3: BI-ENCODER & BONUS/PENALTY (TẦNG 3) ---
        if query_vec is None:
            query_vec = self.bi_model.encode(query_str, convert_to_tensor=True)
        
        all_docs_text = [c['all_text'] for c in top_n]
        doc_vectors = self.bi_model.encode(all_docs_text, convert_to_tensor=True, batch_size=16)
        
        cos_scores = util.cos_sim(query_vec, doc_vectors)[0]
        query_specs = self.extract_tech_specs(query_str)
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_n):
            s_cross = 1 / (1 + np.exp(-cross_scores[i]))
            s_bi = float(cos_scores[i])
            
            # Tính Bonus thông số
            bonus = 0
            doc_text_low = c['all_text'].lower()
            for spec in query_specs:
                if spec in doc_text_low: bonus += 0.15
            for num in query_numbers:
                if len(num) >= 2 and num in doc_text_low: bonus += 0.05

            # Hình phạt
            penalty = 0
            if "sealant" in q_low and "van" in doc_text_low: penalty = 0.4
            if "hcl" in q_low and "naoh" in doc_text_low: penalty = 0.6

            # Trọng số: 60% Cross + 25% Bi + 15% Whoosh
            w_norm = min(c['w_score'] / 50, 1.0)
            final_score = (s_cross * 0.6) + (s_bi * 0.25) + (w_norm * 0.15) + bonus - penalty
            c['final_score'] = float(max(min(final_score, 1.0), 0.0))

        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Xóa all_text trước khi trả về để nhẹ data
        for item in top_n: item.pop('all_text', None)
        return top_n[:top_k]

    def search_batch(self, queries, top_k=1):
        """Xử lý hàng loạt queries tối ưu cho i5 6 nhân"""
        if not queries: return []
        
        query_embs = self.bi_model.encode(queries, convert_to_tensor=True, batch_size=32)
        
        all_results = []
        for i, q_str in enumerate(queries):
            res = self.search(q_str, top_k=top_k, query_vec=query_embs[i])
            all_results.append(res)
        return all_results