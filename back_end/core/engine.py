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
    def search_batch(self, queries, top_k=1):
        """
        Xử lý hàng loạt queries để tận dụng Batch Encoding của Bi-Encoder
        """
        if not queries: return []
        
        # --- BƯỚC TỐI ƯU QUAN TRỌNG NHẤT ---
        # Encode toàn bộ danh sách query từ Word trong 1 lần duy nhất
        # query_embs sẽ là một ma trận (số lượng query x 1024)
        query_embs = self.bi_model.encode(queries, convert_to_tensor=True, batch_size=32)
        
        all_results = []
        
        # Sau khi có toàn bộ Vector, ta mới lặp để xử lý tầng Whoosh và Cross-Encoder
        for i, query_str in enumerate(queries):
            # Lấy vector tương ứng của query thứ i
            current_vec = query_embs[i]
            
            # Gọi một hàm search tùy chỉnh (hoặc sửa hàm search cũ) 
            # để nhận thêm tham số 'query_vec' đã tính sẵn
            result = self.search(query_str, query_vec=current_vec, top_k=top_k)
            all_results.append(result)
            
        return all_results
    def search(self, query_str, top_k=15, query_vec=None):
        """
        Hàm search lai ghép: Hỗ trợ cả tìm kiếm đơn lẻ và hàng loạt (qua query_vec)
        """
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
            
            # Lấy 60 ứng viên
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
        top_n = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_n]
        cross_scores = self.cross_model.predict(pairs, batch_size=16)

        # --- BƯỚC 3: BI-ENCODER & LOGIC THƯỞNG/PHẠT (TẦNG 3) ---
        
        # KIỂM TRA VECTOR: Nếu chưa có (search đơn lẻ) thì mới encode
        if query_vec is None:
            query_vec = self.bi_model.encode(query_str, convert_to_tensor=True)
        
        all_docs_text = [c['all_text'] for c in top_n]
        # Vẫn encode docs của ứng viên (vì docs này thay đổi theo từng query)
        doc_vectors = self.bi_model.encode(all_docs_text, convert_to_tensor=True, batch_size=16)
        
        # Tính Cosine Similarity
        cos_scores = util.cos_sim(query_vec, doc_vectors)[0]
        
        # Lấy thông số kỹ thuật để tính bonus
        query_specs = self.extract_tech_specs(query_str)
        query_numbers = re.findall(r'\d+', query_str)

        for i, c in enumerate(top_n):
            # 1. Điểm Cross-Encoder
            s_cross = 1 / (1 + np.exp(-cross_scores[i]))
            
            # 2. Điểm Bi-Encoder
            s_bi = float(cos_scores[i])
            
            # 3. Logic Thưởng
            bonus = 0
            doc_text_low = c['all_text'].lower()
            for spec in query_specs:
                if spec in doc_text_low: bonus += 0.15
            for num in query_numbers:
                if len(num) >= 2 and num in doc_text_low: bonus += 0.05

            # 4. Hình phạt
            penalty = 0
            if "sealant" in q_low and "van" in doc_text_low: penalty = 0.4
            if "hcl" in q_low and "naoh" in doc_text_low: penalty = 0.6

            # TỔNG HỢP (60% Cross + 25% Bi + 15% Whoosh)
            c['ai_relevance'] = float(s_cross)
            w_norm = min(c['w_score'] / 50, 1.0)
            final_score = (s_cross * 0.6) + (s_bi * 0.25) + (w_norm * 0.15) + bonus - penalty
            c['final_score'] = float(max(min(final_score, 1.0), 0.0))

        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        for item in top_n:
            item.pop('all_text', None)
            
        return top_n[:top_k]

    def search_batch(self, queries, top_k=1):
        """
        Hàm thực hiện tìm kiếm hàng loạt tối ưu CPU
        """
        if not queries: return []
        
        # Encode toàn bộ danh sách query 1 lần duy nhất bằng Batch mode
        # batch_size=32 giúp tận dụng 6 nhân i5 cực tốt
        query_embs = self.bi_model.encode(queries, convert_to_tensor=True, batch_size=32)
        
        all_results = []
        for i, q_str in enumerate(queries):
            # Truyền query_vec đã tính sẵn vào hàm search
            res = self.search(q_str, top_k=top_k, query_vec=query_embs[i])
            all_results.append(res)
            
        return all_results