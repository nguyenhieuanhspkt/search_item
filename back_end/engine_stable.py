import os
import numpy as np
import re
import torch
import logging
from sentence_transformers import SentenceTransformer, util, CrossEncoder
from whoosh.index import open_dir, exists_in
from whoosh.qparser import MultifieldParser, OrGroup

# Cấu hình Logging để Telemetry nhẹ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SearchEngine")

class HybridSearchEngine:
    def __init__(self, model_path=None, index_dir="vattu_index"):
        self.index_dir = index_dir
        
        # 1. Model Bi-Encoder fallback theo cấu hình (BGE-M3 mặc định)
        if model_path is None:
            model_path = os.getenv("BI_ENCODER_MODEL", r"D:\TaskApp_pro\AI_models\BGE")
        
        logger.info(f"Loading Bi-Encoder: {model_path}")
        self.bi_model = SentenceTransformer(model_path, device='cpu')
        
        # 2. Cross-Encoder (Reranker)
        self.cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')
        
        # Tối ưu CPU 6 nhân
        torch.set_num_threads(4)

    def extract_tech_specs(self, text):
        """Mở rộng để bao phủ mọi ngành từ kỹ thuật đến tiêu dùng"""
        # Thêm các đơn vị phổ biến của nhiều ngành khác nhau
        # gsm (giấy), l/ml (hóa chất), m2/m3 (xây dựng), % (nồng độ),...
        pattern = r'(\d+[\.,]?\d*\s*(?:kw|w|v|vac|vdc|a|dn|hp|mm|cm|m|m2|m3|kg|g|mg|l|ml|gsm|inch|psi|bar|kpa|rpm|hz|phi|ø|°c|%|x))'
        return re.findall(pattern, text.lower())

    def extract_brands_materials(self, text):
        """Nhận diện Hãng sản xuất và Vật liệu (Bonus đặc biệt)"""
        brands = ['skf', 'siemens', 'toyo', 'abb', 'schneider', 'mitsubishi', 'danfoss', 'festo']
        materials = ['ss304', 'ss316', 'pvc', 'ptfe', 'inox', 'thep', 'dong', 'nhua']
        
        found_brands = [b for b in brands if b in text.lower()]
        found_mats = [m for m in materials if m in text.lower()]
        return found_brands, found_mats

    def search(self, query_str, top_k=15):
        if not exists_in(self.index_dir): return []
        
        ix = open_dir(self.index_dir)
        q_low = query_str.lower()
        
        # --- BƯỚC 1: WHOOSH LỌC NHANH ---
        candidates = []
        with ix.searcher() as searcher:
            og = OrGroup.factory(0.5)
            parser = MultifieldParser(["ten_vattu", "thong_so", "all_text"], ix.schema, group=og)
            query = parser.parse(query_str) # Giữ nguyên query gốc để Whoosh tự xử lý
            results = searcher.search(query, limit=60)
            
            for hit in results:
                candidates.append({
                    "ma": hit.get('ma_vattu', ''),
                    "ten": hit.get('ten_vattu', ''),
                    "ts": hit.get('thong_so', ''),
                    "hang": hit.get('hang_sx', ''),
                    "dvt": hit.get('dvt', 'N/A'),
                    "all_text": hit.get('all_text', ''),
                    "w_score": hit.score,
                    "telemetry": [] # Lưu log các yếu tố ảnh hưởng
                })

        # --- FAIL-SOFT: Nếu Whoosh rỗng, bạn có thể thực hiện Vector Search ở đây ---
        if not candidates: 
            logger.warning(f"Whoosh found 0 candidates for: {query_str}")
            return []

        # --- BƯỚC 2: CROSS-ENCODER RERANKING (Batch size tối ưu) ---
        top_n = candidates[:30]
        pairs = [[query_str, c['all_text']] for c in top_n]
        cross_scores = self.cross_model.predict(pairs, batch_size=16)

        # --- BƯỚC 3: BI-ENCODER (Tối ưu batch encode=64) ---
        query_vec = self.bi_model.encode(query_str, convert_to_tensor=True)
        all_docs_text = [c['all_text'] for c in top_n]
        doc_vectors = self.bi_model.encode(all_docs_text, convert_to_tensor=True, batch_size=64)
        cos_scores = util.cos_sim(query_vec, doc_vectors)[0]

        # Trích xuất đặc trưng query
        q_specs = self.extract_tech_specs(query_str)
        q_brands, q_mats = self.extract_brands_materials(query_str)

        for i, c in enumerate(top_n):
            doc_text = c['all_text']
            doc_text_low = doc_text.lower()
            
            # 1. Điểm AI cơ bản
            s_cross = 1 / (1 + np.exp(-cross_scores[i]))
            s_bi = float(cos_scores[i])
            
            # 2. Thưởng Spec & Brand
            bonus = 0
            # Thưởng Spec (kW, V, Bar...)
            match_specs = [s for s in q_specs if s in doc_text_low]
            if match_specs:
                bonus += 0.08 * len(match_specs)
                c['telemetry'].append(f"Match specs: {match_specs}")

            # Thưởng Hãng & Vật liệu
            match_brands = [b for b in q_brands if b in doc_text_low]
            match_mats = [m for m in q_mats if m in doc_text_low]
            if match_brands: 
                bonus += 0.1
                c['telemetry'].append(f"Match brand: {match_brands}")
            if match_mats: 
                bonus += 0.05
                c['telemetry'].append(f"Match material: {match_mats}")

            # 3. Exact Case Match (Mã hiệu nhạy cảm hoa thường)
            if any(word in doc_text for word in query_str.split() if word.isupper() and len(word) > 2):
                bonus += 0.05
                c['telemetry'].append("Exact case match detected")

            # 4. Penalty (Logic cũ)
            penalty = 0
            if "sealant" in q_low and "van" in doc_text_low: penalty = 0.3
            
            # Công thức tổng hợp (Trọng số điều chỉnh)
            w_norm = min(c['w_score'] / 50, 1.0)
            final_score = (s_cross * 0.55) + (s_bi * 0.25) + (w_norm * 0.20) + bonus - penalty
            
            c['ai_relevance'] = float(s_cross)
            c['final_score'] = float(max(min(final_score, 1.0), 0.0))

        top_n.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Cleanup telemetry trước khi trả về nếu không cần debug ở UI
        # for item in top_n: item.pop('all_text', None) 
        
        return top_n[:top_k]