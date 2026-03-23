# core2/engine.py
from typing import List, Optional
from .db import DB
from .config import Config
from .dictionary import normalize_candidates
from .retriever import retrieve
from .validator import validate_hits
from .schemas import EngineResult, Candidate, ValidationIssue

class SearchEngine:
    def __init__(self, db_path: str = "core2/entities.db"):
        # Khởi tạo các thành phần dùng chung
        self.db = DB(db_path)
        self.cfg = Config()

    def search(self, raw_candidates: List[Candidate]) -> EngineResult:
        """
        Luồng xử lý chính (Pipeline):
        Dictionary -> Retriever -> Validator -> Result
        """
        # 1. Chuẩn hóa (Xử lý Alias, Synonyms)
        normalized_cands = normalize_candidates(self.db, raw_candidates)
        
        # 2. Truy xuất (Lấy sản phẩm từ DB - Hybrid Search)
        hits = retrieve(self.db, normalized_cands, self.cfg)
        
        # 3. Thẩm định (Lọc hãng, phạt điểm, gắn cảnh báo)
        final_hits = validate_hits(hits, normalized_cands, self.cfg)
        
        # 4. Đóng gói kết quả
        selected_id = final_hits[0].product_id if final_hits else None
        top_score = final_hits[0].combined if final_hits else 0.0
        
        # Tạo danh sách issue từ reasons của các hit (nếu có penalty)
        issues = []
        if final_hits and any("Penalty" in r for r in final_hits[0].reasons):
            issues.append(ValidationIssue(
                code="BRAND_MISMATCH",
                message=f"Sản phẩm tìm thấy không khớp với hãng yêu cầu.",
                penalty=0.8
            ))

        return EngineResult(
            input_text=" ".join([c.raw_text for c in raw_candidates]),
            candidates=normalized_cands,
            primary_model=None, # Có thể mở rộng để trả về ScoredModel riêng
            hits=final_hits,
            issues=issues,
            final_score=top_score,
            selected_product_id=selected_id
        )

    def close(self):
        self.db.close()