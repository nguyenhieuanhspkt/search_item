import sys
import os
from pathlib import Path

# Thêm đường dẫn để Python nhận diện được package core2
sys.path.append(os.getcwd())

from core2.db import DB
from core2.config import Config
from core2.dictionary import normalize_candidates
from core2.retriever import retrieve
from core2.validator import validate_hits
from core2.schemas import Candidate

# 1. Khởi tạo các thành phần
db_path = "core2/entities.db"
if not os.path.exists(db_path):
    print(f"❌ Không tìm thấy file DB tại {db_path}. Vui lòng chạy seed_data.py trước!")
    sys.exit()

db = DB(db_path)
cfg = Config()

def run_engine_test(title, raw_input_list):
    print(f"\n{'='*20} {title} {'='*20}")
    print(f"Input: {[c.raw_text for c in raw_input_list]}")

    # BƯỚC 1: Dictionary (Chuẩn hóa Alias '62052RS' -> '6205-2RS')
    cands = normalize_candidates(db, raw_input_list)
    print(f"-> Sau chuẩn hóa: {[c.normalized for c in cands]}")

    # BƯỚC 2: Retriever (Lấy sản phẩm từ DB)
    hits = retrieve(db, cands, cfg)
    
    # BƯỚC 3: Validator (Lọc hãng, phạt điểm nếu sai)
    final_hits = validate_hits(hits, cands, cfg)

    if not final_hits:
        print("--- ❌ KHÔNG TÌM THẤY KẾT QUẢ PHÙ HỢP ---")
    else:
        for i, h in enumerate(final_hits[:3]):
            print(f"{i+1}. [{h.brand}] {h.name}")
            print(f"   Mã chuẩn: {h.model_code} | Điểm: {h.combined:.2f}")
            if h.reasons:
                print(f"   Lý do: {', '.join(h.reasons)}")

# --- CHẠY CÁC KỊCH BẢN ---

# Kịch bản 1: Test Alias (Gõ sai mã hiệu nhưng máy vẫn phải hiểu)
run_engine_test("TEST 1: ALIAS MATCH (BẮN TỈA)", [
    Candidate(raw_text="62052RS", normalized="62052RS", type_hint="model")
])

# Kịch bản 2: Test Keyword + Synonym (inox -> SUS304)
run_engine_test("TEST 2: KEYWORD & SYNONYM", [
    Candidate(raw_text="tấm inox", normalized="tấm inox", type_hint="text")
])

# Kịch bản 3: Test Brand Mismatch (Tìm mã này nhưng đòi hãng khác)
# Giả sử trong DB mã 6205-2RS là của SKF, nhưng user đòi hãng OMRON
run_engine_test("TEST 3: SAI HÃNG (BRAND PENALTY)", [
    Candidate(raw_text="6205-2RS", normalized="6205-2RS", type_hint="model"),
    Candidate(raw_text="OMRON", normalized="OMRON", type_hint="brand")
])

db.close()