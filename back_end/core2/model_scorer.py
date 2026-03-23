# core2/model_scorer.py
from typing import Optional, List
from .schemas import Candidate, ScoredModel
from .db import DB
from .config import Config

def _simple_similarity(a: str, b: str) -> float:
    # Demo: Jaccard ký tự — thay bằng fuzzywuzzy/rapidfuzz ở bản thật
    sa, sb = set(a.lower()), set(b.lower())
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)

def score_model_candidate(
    db: DB, cand: Candidate, cfg: Config, prefer_brand: Optional[str] = None
) -> Optional[ScoredModel]:
    if cand.type_hint != "model":
        return None

    # Tìm các sản phẩm có model_code = cand.normalized (hoặc tương đương)
    exact = db.fetch_products_by_model_brand(cand.normalized, prefer_brand)
    if exact:
        return ScoredModel(
            model_code=cand.normalized,
            brand=prefer_brand or exact[0]["brand"],
            score=1.0,
            priority_pass=True,
            reasons=["Exact model_code match"]
        )

    # Nếu không exact, thử LIKE fallback
    rows = db.search_like(cand.normalized, limit=8)
    best = None
    best_score = 0.0
    for r in rows:
        sim = _simple_similarity(cand.normalized, r["model_code"])
        if sim > best_score:
            best = r
            best_score = sim

    if best and best_score >= cfg.thresholds.reject:
        pri = best_score >= cfg.thresholds.exact_priority
        return ScoredModel(
            model_code=best["model_code"],
            brand=best["brand"],
            score=float(best_score),
            priority_pass=bool(pri),
            reasons=[f"LIKE search + char-jaccard={best_score:.2f}"],
            extra={"product_id": best["id"]}
        )
    return None