from typing import List, Optional
from .schemas import RetrievalHit, Candidate
from .db import DB
from .config import Config
from .model_scorer import score_model_candidate

class KeywordBackend:
    def __init__(self, db: DB):
        self.db = db

    def search(self, query: str, limit=20) -> List[RetrievalHit]:
        rows = self.db.search_like(query, limit=limit)
        hits = []
        for r in rows:
            # Truy cập kiểu row["key"] an toàn cho sqlite3.Row
            try:
                # Kiểm tra xem kscore có trong các cột trả về không
                k_score = float(r["kscore"]) if "kscore" in r.keys() else 0.5
            except:
                k_score = 0.5

            hits.append(RetrievalHit(
                product_id=r["id"],
                model_code=r["model_code"],
                brand=r["brand"],
                name=r["name"],
                score_keyword=k_score,
                reasons=["Keyword match"]
            ))
        return hits

class VectorBackend:
    def search(self, query: str, limit=20) -> List[RetrievalHit]:
        return []

def combine_scores(kw_hits: List[RetrievalHit], 
                   vec_hits: List[RetrievalHit], 
                   cfg: Config) -> List[RetrievalHit]:
    by_id = {h.product_id: h for h in kw_hits}
    for v in vec_hits:
        if v.product_id in by_id:
            by_id[v.product_id].score_vector = v.score_vector
        else:
            by_id[v.product_id] = v
            
    out = []
    for h in by_id.values():
        # Dùng các giá trị từ config.py đã sửa ở trên
        h.combined = (cfg.weights.keyword * h.score_keyword) + \
                     (cfg.weights.vector * h.score_vector)
        out.append(h)
    
    out.sort(key=lambda x: x.combined, reverse=True)
    return out

def retrieve(db: DB, candidates: List[Candidate], cfg: Config) -> List[RetrievalHit]:
    # 1. ƯU TIÊN MODEL MATCH (Priority Pass)
    for cand in candidates:
        if cand.type_hint == "model":
            scored = score_model_candidate(db, cand, cfg)
            if scored and scored.priority_pass:
                products = db.fetch_products_by_model_brand(scored.model_code, scored.brand)
                if products:
                    return [RetrievalHit(
                        product_id=p["id"],
                        model_code=p["model_code"],
                        brand=p["brand"],
                        name=p["name"],
                        score_keyword=1.0,
                        combined=1.0,
                        reasons=["Priority: Exact Model Match"]
                    ) for p in products]

    # 2. HYBRID SEARCH
    query_str = " ".join([c.normalized for c in candidates])
    kw_backend = KeywordBackend(db)
    vec_backend = VectorBackend()
    
    top_k = cfg.search.top_k if hasattr(cfg, 'search') else 20
    kw_hits = kw_backend.search(query_str, limit=top_k)
    vec_hits = vec_backend.search(query_str, limit=top_k)
    
    return combine_scores(kw_hits, vec_hits, cfg)