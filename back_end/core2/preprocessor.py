# core2/preprocessor.py
import re
from typing import List
from .schemas import Candidate

def run(text: str) -> List[Candidate]:
    # 1. Làm sạch sơ bộ
    text = text.strip()
    
    # 2. Định nghĩa các Pattern "đặc sản" của Vĩnh Tân 4
    # Ví dụ: Mã hiệu thường có gạch ngang và số
    model_pattern = r'[A-Z0-9]+[\-\.\/][A-Z0-9]+' 
    
    # 3. Trích xuất
    candidates = []
    
    # Tìm Model
    models = re.findall(model_pattern, text.upper())
    for m in models:
        candidates.append(Candidate(raw_text=m, normalized=m, type_hint="model"))
        text = text.replace(m, "") # Xóa mã đã tìm để tránh trùng lặp
        
    # 4. Phần còn lại coi như text tự do (remainder)
    remainder = text.strip()
    if remainder:
        candidates.append(Candidate(raw_text=remainder, normalized=remainder, type_hint="text"))
        
    return candidates