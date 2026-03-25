import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# 1. THIẾT LẬP ĐƯỜNG DẪN (PATH SETUP)
# ============================================================
current_file = Path(__file__).resolve()
# AI_SYSTEM_DIR: folder 'ai_audit_system' (chứa pipeline.py)
AI_SYSTEM_DIR = current_file.parent 
# PROJECT_ROOT: lùi 4 tầng về 'TaskApp' (Dựa trên cấu trúc folder của Hiếu)
PROJECT_ROOT = current_file.parents[4] 

# Nạp AI_SYSTEM_DIR vào đầu danh sách tìm kiếm để gọi 'from pipeline ...'
if str(AI_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SYSTEM_DIR))

# Nạp PROJECT_ROOT để hỗ trợ các import từ các folder con khác
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

print("="*60)
print(f"📍 Root dự án: {PROJECT_ROOT}")
print(f"📍 AI System Path: {AI_SYSTEM_DIR}")

# --- IMPORT PIPELINE ---
try:
    # Import class đã chuẩn hóa từ file pipeline.py
    from pipeline import MaterialAuditPipeline
    print("✅ Kết nối Pipeline thành công!")
except Exception as e:
    print(f"❌ Lỗi Import nghiêm trọng: {e}")
    sys.exit(1)

# --- ĐỊNH VỊ CÁC FILE DỮ LIỆU ---
DATA_DIR = AI_SYSTEM_DIR / "data"
INPUT_FILE = DATA_DIR / "raw" / "Your_102_items.xlsx"
ERP_MASTER  = DATA_DIR / "raw" / "Data_For_Meili.xlsx"

# Nơi chứa Index FAISS (Bộ nhớ AI)
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_FILE = PROCESSED_DIR / "faiss.index"
META_FILE  = PROCESSED_DIR / "faiss_meta.pkl" 

# File kết quả xuất ra Excel
OUTPUT_FILE = PROCESSED_DIR / f"Ket_Qua_Tham_Dinh_{datetime.now().strftime('%d%m_%H%M')}.xlsx"

# ============================================================
# 2. CHƯƠNG TRÌNH CHÍNH (MAIN LOGIC)
# ============================================================
def main():
    print("="*60)
    print("🚀 HỆ THỐNG AI THẨM ĐỊNH VẬT TƯ - VĨNH TÂN 4")
    print(f"⏰ Bắt đầu lúc: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)

    # 1. Khởi tạo Pipeline
    try:
        # Trỏ vào folder 'config' nằm cùng cấp với main.py
        pipe = MaterialAuditPipeline(config_path="config")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Pipeline: {e}")
        return

    # 2. QUẢN LÝ BỘ NHỚ AI (FAISS)
    if INDEX_FILE.exists() and META_FILE.exists():
        print(f"✅ Đang nạp Bộ nhớ AI từ: {INDEX_FILE.name}")
        pipe.load_index(str(INDEX_FILE), str(META_FILE))
    else:
        print("⚠️  Không tìm thấy Bộ nhớ AI (FAISS). Đang tiến hành xây dựng mới...")
        if not ERP_MASTER.exists():
            print(f"❌ Lỗi: Không thấy file ERP gốc tại {ERP_MASTER}")
            return
        
        # Tự tạo folder processed nếu chưa có
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        pipe.build_index(str(ERP_MASTER), str(INDEX_FILE), str(META_FILE))

    # 3. ĐỌC DANH SÁCH 102 MÓN CẦN THẨM ĐỊNH
    if not INPUT_FILE.exists():
        print(f"❌ Lỗi: Không tìm thấy file đầu vào tại:\n{INPUT_FILE}")
        return
        
    print(f"📖 Đang đọc danh sách thẩm định: {INPUT_FILE.name}")
    try:
        df_input = pd.read_excel(INPUT_FILE)
        
        # 4. CHẠY THẨM ĐỊNH (AI Audit Batch)
        print(f"🔍 AI đang đối chiếu dữ liệu (Extract -> Score -> Explain)...")
        # Gọi hàm process đã viết trong pipeline.py
        df_out = pipe.process(df_input)

        # 5. XUẤT KẾT QUẢ RA EXCEL
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_excel(OUTPUT_FILE, index=False)
        
        print("\n" + "="*60)
        print(f"✨ THẨM ĐỊNH HOÀN TẤT!")
        print(f"💾 File kết quả: {OUTPUT_FILE.name}")
        print(f"📍 Lưu tại: {PROCESSED_DIR}")
        print("="*60)

    except Exception as e:
        print(f"❌ Lỗi trong quá trình xử lý: {e}")

# ============================================================
# 3. ĐIỂM KÍCH HOẠT (ENTRY POINT)
# ============================================================
if __name__ == "__main__":
    main()