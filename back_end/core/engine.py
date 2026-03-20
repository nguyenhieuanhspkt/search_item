# search_item/back_end/core/engine.py
from __future__ import annotations
from typing import List, Dict, Optional, Any
import gc
import pandas as pd
import os
import json
import re
import numpy as np
import torch
from .config import RankConfig
from .helpers import (
    clean_query_text,
    minmax_norm,
    normalize_bi_scores,
    extract_all_numbers,
    predict_category_batch,
    clamp01,
)
from .retrievers import WhooshRetriever
from .scorers import create_scorers
from .rules import BusinessRules
from .ranker import HeuristicRanker


class HybridSearchEngine:
    """
    Nhạc trưởng điều phối Pipeline Tìm kiếm Lai (Hybrid Search):
    Quy trình: Lexical (Whoosh) -> Semantic (Bi+Cross) -> Rules -> Ranker.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        index_dir: Optional[str] = None,
        cfg: Optional[RankConfig] = None,
        device: str = "cpu",
        threads: Optional[int] = None,
    ) -> None:
        # 1. Khởi tạo cấu hình (Config)
        self.cfg = cfg or RankConfig()
        
        # Xác định số luồng CPU tối ưu (Ưu tiên lấy từ Config)
        num_threads = threads or getattr(self.cfg, 'set_num_threads', 4)

        # 2. Thiết lập đường dẫn
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(self.current_dir)

        # 3. Nạp dữ liệu Chủng loại (Categories)
        self.cat_path = os.path.join(self.current_dir, "categories.json")
        self.category_data = self._load_categories()
        self.category_names = list(self.category_data.keys())
        self._cat_vectors = None

        # 4. Cấu hình Model & Index
        local_bge_path = os.path.join(backend_dir, "AI_models", "BGE")
        final_bi_model = model_path or (local_bge_path if os.path.exists(local_bge_path) else "keepitreal/vietnamese-sbert")
        
        
        local_cross_path = os.path.join(backend_dir, "AI_models", "cross-encoder")
        final_cross_model = local_cross_path if os.path.exists(local_cross_path) else "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self.index_dir = index_dir or os.path.join(backend_dir, "vattu_index")

        # 5. Khởi tạo các Sub-modules (Linh kiện)
        self.retriever = WhooshRetriever(index_dir=self.index_dir)
        
        # Scorers (Bi + Cross Encoder)
        self.scorers = create_scorers(
            bi_model_path=final_bi_model,
            cross_model_path=final_cross_model,
            device=device,
            bi_batch=16,
            cross_batch=16,
            cross_is_logit=self.cfg.cross_is_logit,
            threads=num_threads,
        )
        # --- CHÈN VÀO ĐÂY: Dọn dẹp RAM ngay sau khi nạp Model ---
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # -------------------------------------------------------

        # Rules & Ranker (Trọng tài & Bộ não hợp điểm)
        self.rules = BusinessRules(
            cap_bonus=self.cfg.cap_bonus,
            cap_penalty=self.cfg.cap_penalty,
        )
        self.ranker = HeuristicRanker(self.cfg)

        # Tính sẵn vector chủng loại để tăng tốc build index
        if self.category_names:
            try:
                self._cat_vectors = self.scorers.bi.encode_texts(self.category_names)
            except Exception as e:
                print(f"⚠️ Không thể tính vector chủng loại: {e}")

        print(f"--- ✅ AI Engine Ready (Model: {final_bi_model}) ---")

    def _load_categories(self) -> Dict[str, List[str]]:
        if os.path.exists(self.cat_path):
            try:
                with open(self.cat_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: return {}
        return {}

    def predict_category(self, text: str, threshold: float = 0.55) -> str:
        """Dự đoán chủng loại: Ưu tiên Keyword -> Semantic (AI)."""
        text_low = (text or "").lower()

        # Vòng 1: Khớp từ khóa cứng
        for cat, keywords in self.category_data.items():
            if any(kw in text_low for kw in keywords):
                return cat

        # Vòng 2: AI suy luận (Bi-Encoder)
        if self._cat_vectors is not None:
            try:
                tvec = self.scorers.bi.encode_texts([text])[0]
                # Tính cosine sim (normalize_to_unit=True để map về [0,1])
                sims = self.scorers.bi.cosine_similarities(tvec, self._cat_vectors, normalize_to_unit=True)
                best_idx = int(np.argmax(sims))
                if sims[best_idx] > threshold:
                    return self.category_names[best_idx]
            except Exception: pass

        return "Vật tư khác"

    def build_and_save_index(self, excel_path: str, overwrite: bool = True):
        """
        Quy trình xây dựng Index: Đọc Excel -> Batch AI -> Ghi Index.
        Trả về generator để stream tiến trình về Frontend.
        """
        import pandas as pd
        import os
        from .helpers import predict_category_batch # Đảm bảo đã import hàm này

        if not os.path.exists(excel_path):
            yield {"status": "error", "message": "Không tìm thấy file tạm."}
            return

        try:
            # 1. Đọc dữ liệu
            yield {"status": "info", "message": "📂 Đang đọc file Excel..."}
            df = pd.read_excel(excel_path).fillna("")
            total_rows = len(df)
            
            # 2. Chuẩn bị text
            texts_to_predict = [
                f"{str(r.get('Tên vật tư', ''))} {str(r.get('Thông số kỹ thuật', ''))}".strip() 
                for _, r in df.iterrows()
            ]

            # 3. Dự đoán AI theo Batch
            all_categories = []
            batch_size = 128
            
            yield {"status": "info", "message": f"🤖 Đang phân loại AI cho {total_rows} dòng..."}

            for i in range(0, total_rows, batch_size):
                chunk = texts_to_predict[i : i + batch_size]
                
                # Sử dụng hàm helper đã viết trong helpers.py
                chunk_cats = predict_category_batch(
                    texts=chunk,
                    category_data=self.category_data,
                    category_names=self.category_names,
                    cat_vectors=self._cat_vectors,
                    bi_encoder_model=self.scorers.bi,
                    threshold=0.55
                )
                all_categories.extend(chunk_cats)
                
                # Tính % dựa trên len(df) thực tế
                current_count = min(i + batch_size, total_rows)
                percent = round((current_count / total_rows) * 100, 2)
                
                # Bắn dữ liệu tiến độ về API
                yield {
                    "status": "progress", 
                    "percent": percent, 
                    "current": current_count, 
                    "total": total_rows
                }

            # 4. Ghi vào Whoosh
            yield {"status": "info", "message": "💾 Đang ghi dữ liệu vào Index..."}
            success = self.retriever.build_index_from_dataframe(
                df=df,
                categories_list=all_categories,
                overwrite=overwrite
            )

            if success:
                yield {"status": "success", "message": "✨ Nạp dữ liệu thành công!"}
            else:
                yield {"status": "error", "message": "Lỗi khi ghi index."}

        except Exception as e:
            yield {"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}

    def extract_tech_specs(self, text: str) -> List[str]:
        """Trích xuất 'số + đơn vị' (VD: 200mm, DN50, phi60)."""
        if not text: return []
        t = text.lower().replace("ø", "o").replace("φ", "o")
        # Pattern cải tiến bắt cả số lẻ và đơn vị kỹ thuật
        pattern = r'\b(?:\d+(?:[\.,]\d+)?\s?(?:mm|cm|m|kw|w|v|a|dn|hp|kg|g|inch|in|")|o\d+|phi\d+|t\d+(?:[\.,]\d+)?|\d+x\d+)\b'
        return list(set(re.findall(pattern, t)))

    def extract_important_codes(self, text: str) -> List[str]:
        """Trích xuất mã hiệu vật liệu/kỹ thuật (VD: SA240, 310S)."""
        if not text: return []
        return re.findall(r'([a-zA-Z]+\d+\w*|\d+[a-zA-Z]+\w*)', text.upper())

    def search(
        self,
        query_str: str,
        top_k: int = 15,
        query_vec: Optional[torch.Tensor] = None,
        explain: bool = False,
    ) -> List[Dict]:
        """Hàm tìm kiếm cốt lõi của hệ thống."""
        if not self.retriever.exists(): return []

        # 1. TẦNG 1: LEXICAL RETRIEVAL (WHOOSH)
        clean_q = clean_query_text(query_str)
        candidates = self.retriever.search(clean_q, limit=self.cfg.whoosh_limit)
        if not candidates: return []

        # Chuẩn hóa điểm Whoosh theo batch
        w_norm_arr = minmax_norm([c["w_score"] for c in candidates])
        for c, w in zip(candidates, w_norm_arr):
            c["_w_norm"] = float(w)

        # 2. TẦNG 2: SEMANTIC SCORING (RERANKING)
        top_n = candidates[:self.cfg.rerank_top_n]
        texts = [c["all_text"] for c in top_n]

        # A) Cross-Encoder (Deep match)
        pairs = [(query_str, t) for t in texts]
        s_cross_arr = self.scorers.cross.score_pairs(pairs)

        # B) Bi-Encoder (Cosine Similarity)
        q_vec = query_vec if query_vec is not None else self.scorers.bi.encode_query(query_str)
        doc_vecs = self.scorers.bi.encode_texts(texts)
        s_bi_arr = self.scorers.bi.get_scores(q_vec, doc_vecs)

        # 3. TẦNG 3: BUSINESS RULES & FUSION
        q_specs = self.extract_tech_specs(query_str)
        q_codes = self.extract_important_codes(query_str)
        q_numbers = extract_all_numbers(query_str)

        results = []
        for i, c in enumerate(top_n):
            # Tính thưởng/phạt
            bonus, penalty, reasons = self.rules.compute_bonus_penalty(
                query_str=query_str,
                doc_text=c["all_text"],
                q_codes=q_codes,
                q_specs=q_specs,
                q_numbers=q_numbers,
                explain=explain,
            )

            # Hợp nhất điểm qua Ranker
            final_score, details = self.ranker.score(
                s_cross=float(s_cross_arr[i]),
                s_bi=float(s_bi_arr[i]),
                w_norm=float(c["_w_norm"]),
                bonus=bonus,
                penalty=penalty
            )

            # Đóng gói kết quả
            res_item = {
                "ma_vattu": c["ma"],
                "ten_vattu": c["ten"],
                "thong_so": c["ts"],
                "hang_sx": c["hang"],
                "chung_loai": c["chung_loai"],
                "dvt": c["dvt"],
                "final_score": final_score
            }
            if explain:
                res_item["explain"] = {**details, "why": reasons}
            
            results.append(res_item)

        # Sắp xếp và trả kết quả
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:top_k]

    def search_batch(self, queries: List[str], top_k: int = 1, explain: bool = False) -> List[List[Dict]]:
        """Xử lý tìm kiếm hàng loạt (Tối ưu CPU)."""
        if not queries: return []
        q_vecs = self.scorers.bi.encode_texts(queries)
        return [self.search(q, top_k=top_k, query_vec=q_vecs[i], explain=explain) for i, q in enumerate(queries)]
    
    