import os
import numpy as np
import re
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from whoosh.index import open_dir, exists_in
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path=r'D:\TaskApp_pro\AI_models\BGE', index_dir="vattu_index"):
        self.index_dir = index_dir
        
        # Tối ưu hóa CPU: Sử dụng 4/6 nhân để xử lý AI, chừa 2 nhân cho hệ thống/UI
        torch.set_num_threads(4)
        
        # TẦNG 3: Bi-Encoder - Nâng cấp lên BGE-M3 (Local)
        # Model này cực mạnh trong việc bắt từ khóa ngắn và mã hiệu
        self.bi_model = SentenceTransformer(model_path, device='cpu')
        
        # TẦNG 2: Cross-Encoder (Reranker)
        self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')

    def clean_text(self, text):
        """Làm sạch query nhưng giữ lại các ký tự kỹ thuật quan trọng"""
        if not text: return ""
        # Không xóa dấu chấm (.) và dấu x (trong kích thước 20x30)
        text = re.sub(r'[!"#$%&\'()*+,\-/:;<=>?@[\\\]^_`{|}~]', ' ', text)
        words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
        return " ".join(words)

    def extract_tech_specs(self, text):
        """Trích xuất các thông số kỹ thuật (Số + Đơn vị) để thưởng điểm"""
        # Bắt các dạng: 7.5kw, 220v, dn50, 10hp, 20x30, m10...
        pattern = r'(\d+[\.\,]*\d*\s*(?:kw|v|a|dn|hp|mm|m|kg|inch|phi|ø|\"|x))'
        specs = re.findall(pattern, text.lower())
        return specs

    def search(self, query_str, top_k=15):
        if not exists_in(self.index_dir):
            print("Lỗi: Folder index không tồn tại.")
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
            
            # Tăng lên 60 ứng viên để BGE-M3 có thêm cơ hội lọc
            results = searcher.search(query, limit=60)
            
            for hit in results:
                candidates.append({
                    "ma": hit.get('ma_vattu', ''),
                    "ten": hit.get('ten_vattu', ''),
                    "ts": hit.get('thong_so', ''),
                    "hang": hit.get('hang_sx', ''),
                    "dvt": hit.get('dvt', 'N/A'),
                    "note": hit.get('note', ''),
                    "all_text": hit.get('all_text', ''),
                    "w_score": hit.score
                })
        
        if not candidates:
            return []

        # --- BƯỚC 2: CROSS-ENCODER RERANKING (TẦNG 2) ---
        # Lấy Top 30 để Rerank (Tăng nhẹ từ 25 lên 30 vì BGE-M3 xử lý nhanh)
        top_n = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_n]
        cross_scores = self.cross_model.predict(pairs, batch_size=16)

        # --- BƯỚC 3: BI-ENCODER & LOGIC THƯỞNG/PHẠT (TẦNG 3) ---
        query_vec = self.bi_model.encode(query_str, convert_to_tensor=True)
        all_docs_text = [c['all_text'] for c in top_n]
        doc_vectors = self.bi_model.encode(all_docs_text, convert_to_tensor=True, batch_size=16)
        
        # Tính Cosine Similarity bằng hàm tối ưu của SentenceTransformers
        cos_scores = util.cos_sim(query_vec, doc_vectors)[0]
        
        # Lấy thông số kỹ thuật của Query
        query_specs = self.extract_tech_specs(query_str)
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_n):
            # 1. Điểm Cross-Encoder (Chuẩn hóa Sigmoid)
            s_cross = 1 / (1 + np.exp(-cross_scores[i]))
            
            # 2. Điểm Bi-Encoder (BGE-M3)
            s_bi = float(cos_scores[i])
            
            # 3. Logic Thưởng chuyên sâu
            bonus = 0
            doc_text_low = c['all_text'].lower()
            
            # Thưởng khớp thông số kỹ thuật (Cực kỳ quan trọng cho vật tư)
            for spec in query_specs:
                if spec in doc_text_low:
                    bonus += 0.15 # Thưởng mạnh cho khớp thông số (7.5kw, DN50...)
            
            # Thưởng khớp số lẻ (Mã hiệu)
            for num in query_numbers:
                if len(num) >= 2 and num in doc_text_low:
                    bonus += 0.05

            # 4. Hình phạt (Penalty)
            penalty = 0
            # Phạt nếu sai bản chất (Ví dụ query Van nhưng ra Gioăng/Sealant)
            if "sealant" in q_low and "van" in doc_text_low: penalty = 0.4
            if "hcl" in q_low and "naoh" in doc_text_low: penalty = 0.6

            # CÔNG THỨC TỔNG HỢP CẢI TIẾN
            # Tăng trọng số Cross vì MiniLM Reranker trên CPU rất ổn định
            c['ai_relevance'] = float(s_cross)
            
            # Công thức: 60% Cross + 25% Bi + 15% Whoosh (Điều chỉnh nhẹ tỉ lệ)
            w_norm = min(c['w_score'] / 50, 1.0)
            final_score = (s_cross * 0.6) + (s_bi * 0.25) + (w_norm * 0.15) + bonus - penalty
            
            c['final_score'] = float(max(min(final_score, 1.0), 0.0))

        # Sắp xếp và trả kết quả
        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        for item in top_n:
            item.pop('all_text', None)
            
        return top_n[:top_k]