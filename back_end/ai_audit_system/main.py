# main.py

import os
import pandas as pd
from pathlib import Path
from pipeline import MaterialAuditPipeline

# ============================================================
# 1. XỬ LÝ ĐƯỜNG DẪN ĐỘNG (Dùng cho máy cơ quan & cá nhân)
# ============================================================
# Vị trí file hiện tại: search_item/back_end/ai_audit_system/main.py
current_file = Path(__file__).resolve()

# Root của back_end: search_item/back_end/
back_end_root = current_file.parents[1] 

# Đường dẫn đến các file Excel theo yêu cầu của bạn
ERP_MASTER = back_end_root / "Data_For_Meili.xlsx"
INPUT_FILE = back_end_root / "Your_102_items.xlsx"

# Đường dẫn lưu FAISS Index (lưu tạm trong folder data của ai_audit_system)
DATA_DIR = current_file.parent / "data"
DATA_DIR.mkdir(exist_ok=True) # Tạo folder data nếu chưa có

INDEX_FILE = DATA_DIR / "faiss.index"
META_FILE  = DATA_DIR / "faiss_meta.json"

# File kết quả xuất ra cùng cấp với file main.py
OUTPUT_FILE = current_file.parent / "ERP_Suggestion_Output.xlsx"

# ============================================================
# 2. HÀM THỰC THI CHÍNH
# ============================================================
def main():
    # Khởi tạo Pipeline với đường dẫn config tương đối
    config_path = current_file.parent / "config"
    pipe = MaterialAuditPipeline(config_path=str(config_path))

    # Kiểm tra sự tồn tại của file Master trước khi chạy
    if not ERP_MASTER.exists():
        print(f"❌ Lỗi: Không tìm thấy file ERP Master tại {ERP_MASTER}")
        return

    # Nếu không có index → build index
    if not INDEX_FILE.exists():
        print("⚙️ No FAISS index found → building index...")
        # Ép kiểu Path sang String để các thư viện như pandas/faiss đọc được
        pipe.build_index(str(ERP_MASTER), str(INDEX_FILE), str(META_FILE))

    # Load FAISS
    pipe.load_index(str(INDEX_FILE), str(META_FILE))

    # Load input list
    if not INPUT_FILE.exists():
        print(f"❌ Lỗi: Không tìm thấy file Input tại {INPUT_FILE}")
        return
        
    df_input = pd.read_excel(str(INPUT_FILE), engine="openpyxl")

    # Run pipeline
    print("🚀 Running AI Thẩm định Vật tư...")
    df_out = pipe.process(df_input)

    # Save output
    df_out.to_excel(str(OUTPUT_FILE), index=False)
    print(f"🎉 Done. Output saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()