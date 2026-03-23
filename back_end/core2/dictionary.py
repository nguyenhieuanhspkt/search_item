# core2/dictionary.py
from typing import List
from .schemas import Candidate
from .db import DB

def normalize_candidates(db: DB, cands: List[Candidate]) -> List[Candidate]:
    out = []
    for c in cands:
        # Lấy text gốc để xử lý, loại bỏ khoảng trắng thừa
        text_to_process = c.normalized.strip()
        
        # 1. ƯU TIÊN: Nếu là model, tìm trong bảng model_alias TRƯỚC
        if c.type_hint == "model":
            alias_code = db.find_model_code_by_alias(text_to_process)
            if alias_code:
                # Nếu tìm thấy Alias (62052RS -> 6205-2RS), dùng luôn mã chuẩn này
                text_to_process = alias_code
        
        # 2. Sau đó mới tìm trong bảng synonyms (inox -> SUS304)
        # Nếu đã là mã chuẩn từ bước 1, get_canon thường sẽ trả về None (giữ nguyên)
        final_text = db.get_canon(text_to_process) or text_to_process
        
        out.append(Candidate(
            raw_text=c.raw_text,
            normalized=final_text,
            type_hint=c.type_hint,
            meta=c.meta
        ))
    return out