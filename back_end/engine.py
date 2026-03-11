import os
import numpy as np
import re
from sentence_transformers import SentenceTransformer, CrossEncoder
from whoosh.index import open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser, OrGroup

class HybridSearchEngine:
    def __init__(self, model_path='keepitreal/vietnamese-sbert', index_dir="vattu_index"):
        self.index_dir = index_dir
        
        # TẦNG 3: Bi-Encoder (Nghĩa tổng quát)
        # Dùng để tính toán độ tương đồng Vector (Cosine Similarity)
        self.bi_model = SentenceTransformer(model_path)
        
        # TẦNG 2: Cross-Encoder (Reranker)
        # Chấm điểm cực kỳ chính xác mối quan hệ giữa Query và Document
        self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def clean_text(self, text):
        """Làm sạch query để Whoosh không bị lỗi cú pháp"""
        if not text: return ""
        text = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]', ' ', text)
        words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
        return " ".join(words)

    def search(self, query_str, top_k=15):
        if not exists_in(self.index_dir):
            print("Lỗi: Folder index không tồn tại hoặc rỗng.")
            return []
        
        ix = open_dir(self.index_dir)
        clean_query = self.clean_text(query_str)
        if not clean_query: clean_query = query_str
        
        # --- BƯỚC 1: WHOOSH LỌC NHANH (TẦNG 1) ---
        candidates = []
        with ix.searcher() as searcher:
            # Cho phép khớp 50% từ khóa (OrGroup) để không bỏ sót vật tư
            og = OrGroup.factory(0.5)
            parser = MultifieldParser(["ten_vattu", "thong_so", "all_text"], ix.schema, group=og)
            query = parser.parse(clean_query)
            
            # Lấy 50 ứng viên tiềm năng nhất bằng thuật toán BM25
            results = searcher.search(query, limit=50)
            
            for hit in results:
                candidates.append({
                    "ma": hit.get('ma_vattu', ''),
                    "erp": hit.get('ma_erp', ''),
                    "ten": hit.get('ten_vattu', ''),
                    "ts": hit.get('thong_so', ''),
                    "hang": hit.get('hang_sx', ''), # Quan trọng: lấy field này
                    "dvt": hit.get('dvt', 'N/A'),   # Quan trọng: lấy field này
                    "all_text": hit.get('all_text', ''),
                    "w_score": hit.score # Điểm từ khóa của Whoosh
                })
        
        if not candidates:
            return []

        # --- BƯỚC 2: CROSS-ENCODER RERANKING (TẦNG 2) ---
        # So sánh trực tiếp Query với từng ứng viên (Top 25)
        top_n = candidates[:25]
        pairs = [[query_str, c['all_text']] for c in top_n]
        
        # predict theo mảng (Batch) để tối ưu CPU/GPU
        cross_scores = self.cross_model.predict(pairs)

        # --- BƯỚC 3: BI-ENCODER & LOGIC THƯỞNG/PHẠT (TẦNG 3) ---
        query_vec = self.bi_model.encode(query_str)
        
        # Encode toàn bộ docs trong 1 lần (Batch Encoding) - Giúp search cực nhanh
        all_docs_text = [c['all_text'] for c in top_n]
        doc_vectors = self.bi_model.encode(all_docs_text)
        
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_n):
            # 1. Điểm Cross-Encoder (Thường từ -10 đến 10, đưa về 0-1)
            s_cross = 1 / (1 + np.exp(-cross_scores[i])) # Dùng hàm Sigmoid để chuẩn hóa
            
            # 2. Điểm Bi-Encoder (Cosine Similarity)
            doc_vec = doc_vectors[i]
            s_bi = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-9)
            
            # 3. Thưởng điểm khớp con số (Kích thước, mã hiệu)
            bonus = 0
            text_lower = c['all_text'].lower()
            for num in query_numbers:
                if len(num) >= 2 and num in text_lower:
                    bonus += 0.1 # Thưởng nhẹ để không làm lệch hệ số 0-1
            
            # 4. Hình phạt xung đột (Logic nghiệp vụ)
            penalty = 0
            q_low = query_str.lower()
            if "hcl" in q_low and "naoh" in text_lower: penalty = 0.5
            if "sealant" in q_low and "van" in text_lower: penalty = 0.3

            # CÔNG THỨC TỔNG HỢP (Trọng số 0-1)
            # 60% Cross + 30% Bi + 10% Whoosh
            c['ai_relevance'] = float(s_cross)
            c['final_score'] = (s_cross * 0.6) + (s_bi * 0.3) + (min(c['w_score']/50, 1.0) * 0.1) + bonus - penalty
            
            # Đảm bảo final_score không vượt quá 1.0 và không dưới 0
            c['final_score'] = float(max(min(c['final_score'], 1.0), 0.0))

        # Sắp xếp lại theo điểm tổng hợp
        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Loại bỏ trường all_text trước khi gửi về Front-end để giảm dung lượng tải
        for item in top_n:
            item.pop('all_text', None)
            
        return top_n[:top_k]