from typing import List
from .schemas import RetrievalHit, Candidate
from .config import Config

def validate_hits(hits: List[RetrievalHit], 
                  candidates: List[Candidate], 
                  cfg: Config) -> List[RetrievalHit]:
    """Kiểm tra chéo kết quả với yêu cầu thực tế"""
    # Lấy danh sách hãng người dùng nhắc tới
    target_brands = [c.normalized.upper() for c in candidates if c.type_hint == "brand"]
    
    final_hits = []
    for hit in hits:
        current_score = hit.combined
        
        # Rule: Nếu gõ hãng OMRON mà ra hãng khác -> Phạt nặng
        if target_brands:
            if hit.brand.upper() not in target_brands:
                current_score *= 0.2 # Chỉ giữ lại 20% điểm
                hit.reasons.append(f"Penalty: Brand mismatch (Expected {target_brands})")

        # Loại bỏ nếu điểm quá thấp sau khi phạt
        if current_score < cfg.thresholds.reject:
            continue
            
        hit.combined = current_score
        final_hits.append(hit)
        
    final_hits.sort(key=lambda x: x.combined, reverse=True)
    return final_hits