import os
import sys
import pandas as pd
from pathlib import Path

# ============================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN (PATH SETUP)
# ============================================================
current_file = Path(__file__).resolve()
PROJECT_ROOT = current_file.parent 

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pipeline import MaterialAuditPipeline
except ImportError as e:
    print(f"❌ Lỗi Import: {e}. Hãy đảm bảo main.py và pipeline.py cùng nằm trong ai_audit_system/")
    sys.exit(1)

# --- ĐỊNH VỊ CÁC FILE DỮ LIỆU ---
# Sửa lại đường dẫn INPUT_FILE cho đúng vị trí thực tế của file 102 món
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "Your_102_items.xlsx"
ERP_MASTER  = PROJECT_ROOT / "data" / "raw" / "Data_For_Meili.xlsx"

# Nơi chứa Index từ Colab
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INDEX_FILE = PROCESSED_DIR / "faiss.index"
# ĐỔI TÊN: Dùng .pkl để nạp siêu nhanh thay vì .json
META_FILE  = PROCESSED_DIR / "faiss_meta.pkl" 

# File kết quả xuất ra
OUTPUT_FILE = PROJECT_ROOT /"processed"/"ERP_Suggestion_Output.xlsx"

# ============================================================
# 2. CHƯƠNG TRÌNH CHÍNH
# ============================================================
def main():
    print("="*60)
    print("🚀 HỆ THỐNG THẨM ĐỊNH VẬT TƯ V6.0 - AUTO AUDIT")
    print("="*60)

    # Khởi tạo Pipeline
    pipe = MaterialAuditPipeline(config_path="config")

    # 1. NẠP DỮ LIỆU AI (Ưu tiên nạp từ file đã xử lý trên Colab)
    if INDEX_FILE.exists() and META_FILE.exists():
        print(f"✅ Đang nạp bộ nhớ AI (Index & PKL) từ Colab...")
        pipe.load_index(str(INDEX_FILE), str(META_FILE))
    else:
        print("⚠️  Không thấy file index hoặc meta.pkl. Đang tiến hành Build lại...")
        if not ERP_MASTER.exists():
            print(f"❌ Lỗi: Không tìm thấy file gốc tại {ERP_MASTER}")
            return
        pipe.build_index(str(ERP_MASTER), str(INDEX_FILE), str(META_FILE))

    # 2. ĐỌC FILE 102 MÓN
    if not INPUT_FILE.exists():
        print(f"❌ Lỗi: Không tìm thấy file đầu vào tại:\n{INPUT_FILE}")
        return
        
    print(f"📖 Đang đọc danh sách thẩm định: {INPUT_FILE.name}")
    try:
        df_input = pd.read_excel(INPUT_FILE, engine="openpyxl")
        
        # Kiểm tra nhanh các cột theo ảnh bạn gửi (STT, Mã ERP, Tên, TS)
        required_cols = ['STT', 'Mã ERP', 'Tên', 'TS']
        if not all(col in df_input.columns for col in required_cols):
            print(f"⚠️ Cảnh báo: File Excel thiếu một số cột {required_cols}")
            print(f"🔍 Các cột hiện có trong file: {list(df_input.columns)}")

        # 3. CHẠY THẨM ĐỊNH (AI Audit)
        print(f"🔍 AI đang đối chiếu dữ liệu (Vĩnh Tân 4)...")
        df_out = pipe.process(df_input)

        # 4. XUẤT KẾT QUẢ
        df_out.to_excel(OUTPUT_FILE, index=False)
        print("\n" + "="*60)
        print(f"✨ HOÀN THÀNH!")
        print(f"💾 Kết quả lưu tại: {OUTPUT_FILE.name}")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi xử lý: {e}")

if __name__ == "__main__":
    main()