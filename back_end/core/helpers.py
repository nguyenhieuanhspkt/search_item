# search_item/back_end/core/helpers.py
from __future__ import annotations
import re
import numpy as np
from typing import Iterable, List

# ----------------------------
# 1) CHUẨN HÓA ĐIỂM (Scoring Normalization)
# ----------------------------

def sigmoid(x):
    """Sigmoid để nén điểm logit về dải [0, 1]."""
    return 1.0 / (1.0 + np.exp(-x))

def normalize_cross_scores(raw_scores: Iterable[float], cross_is_logit: bool = True) -> np.ndarray:
    """Chuẩn hóa điểm Cross-Encoder dựa trên cấu hình Config."""
    s = np.asarray(list(raw_scores), dtype=np.float32)
    return sigmoid(s) if cross_is_logit else s

def normalize_bi_scores(cos_scores_np: np.ndarray) -> np.ndarray:
    """Đưa Cosine Similarity từ [-1, 1] về [0, 1] để hợp nhất trọng số."""
    cos_scores_np = np.asarray(cos_scores_np, dtype=np.float32)
    return ((cos_scores_np + 1.0) / 2.0).astype(np.float32)

def minmax_norm(values: Iterable[float]) -> np.ndarray:
    """Chuẩn hóa điểm Whoosh theo batch để tránh việc điểm Whoosh quá cao lấn át AI."""
    arr = np.asarray(list(values), dtype=np.float32)
    if arr.size == 0: return arr
    vmin, vmax = float(np.min(arr)), float(np.max(arr))
    if vmax == vmin: return np.full_like(arr, 0.5)
    return (arr - vmin) / (vmax - vmin)

# ----------------------------
# 2) TRÍCH XUẤT & SO KHỚP SỐ (Numerical Logic)
# ----------------------------

_NUMBER_PATTERN = re.compile(r'\b\d+(?:[\.,]\d+)?\b')

def extract_all_numbers(text: str) -> List[str]:
    """Bắt mọi số đo kỹ thuật."""
    if not text: return []
    return _NUMBER_PATTERN.findall(text)

def numbers_match_ratio(q_numbers: List[str], doc_text: str) -> float:
    """
    Tính tỷ lệ khớp số thông minh. 
    Chuyển tất cả về float để '200' khớp được với '200.0'.
    """
    if not q_numbers: return 0.0
    
    # Trích xuất số từ doc và chuyển về set float để tra cứu nhanh
    try:
        doc_numbers_str = extract_all_numbers(doc_text.lower())
        doc_numbers_float = {float(n.replace(',', '.')) for n in doc_numbers_str}
        
        # Chuyển số từ query về float
        q_floats = []
        for n in q_numbers:
            try: q_floats.append(float(n.replace(',', '.')))
            except: continue
            
        if not q_floats: return 0.0
        
        match_count = sum(1 for n in q_floats if n in doc_numbers_float)
        return match_count / len(q_floats)
    except:
        return 0.0

# ----------------------------
# 3) ĐỊNH DANH TOKEN (Word Boundaries)
# ----------------------------

def has_token(pattern: str, text_lower: str) -> bool:
    """Dùng ranh giới từ để tránh khớp nhầm 'van' trong 'advanced'."""
    if not pattern: return False
    # Thêm re.IGNORECASE để an toàn hơn
    return re.search(rf'\b{re.escape(pattern.lower())}\b', text_lower) is not None

# ----------------------------
# 4) LÀM SẠCH & TIỀN XỬ LÝ
# ----------------------------

def clean_query_text(text: str) -> str:
    """Làm sạch query nhưng bảo vệ các con số và mã hiệu kỹ thuật."""
    if not text: return ""
    # Giữ lại chữ cái, số và khoảng trắng, thay các ký tự lạ thành khoảng trắng
    text = re.sub(r'[!"#$%&\'()*+,\-/:;<=>?@[\\\]^_`{|}~]', ' ', text)
    words = [w for w in text.split() if len(w) > 1 or w.isdigit()]
    return " ".join(words).lower()

def clamp01(x: float) -> float:
    """Đảm bảo điểm cuối cùng luôn nằm trong dải [0, 1] để Frontend hiển thị %."""
    return float(max(min(x, 1.0), 0.0))