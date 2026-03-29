import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from docx import Document  # Thêm dòng này ở đầu file main.py
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
print(f"📂 Thư mục dữ liệu: {DATA_DIR}")
INPUT_FILE = DATA_DIR / "raw" / "Your_102_items.xlsx"
ERP_MASTER  = DATA_DIR / "raw" / "Data_For_Meili.xlsx"

# Nơi chứa Index FAISS (Bộ nhớ AI)
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_FILE = PROCESSED_DIR / "faiss.index"
META_FILE  = PROCESSED_DIR / "faiss_meta.pkl" 

# File kết quả xuất ra Excel
OUTPUT_FILE = PROCESSED_DIR / f"Ket_Qua_Tham_Dinh_{datetime.now().strftime('%d%m_%H%M')}.xlsx"


def read_input_file(file_path):
    suffix = file_path.suffix.lower()
    
    # TRƯỜNG HỢP 1: FILE EXCEL (.xlsx, .xls)
    if suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    
    # TRƯỜNG HỢP 2: FILE WORD (.docx)
    elif suffix == '.docx':
        print(f"📄 Đang trích xuất bảng từ file Word: {file_path.name}")
        doc = Document(file_path)
        data = []
        # Quét qua tất cả các bảng trong file Word
        for table in doc.tables:
            for row in table.rows:
                data.append([cell.text.strip() for cell in row.cells])
        
        if not data:
            raise Exception("Không tìm thấy bảng dữ liệu nào trong file Word!")
            
        # Biến dòng đầu tiên thành tiêu đề (Header)
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    
    else:
        raise Exception(f"Định dạng {suffix} không được hỗ trợ!")


# ============================================================
# 2. CHƯƠNG TRÌNH CHÍNH (MAIN LOGIC)
# ============================================================
def main():
    global INPUT_FILE
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

# 3. ĐỌC DANH SÁCH THẨM ĐỊNH (Hỗ trợ cả Excel và Word)
    print(INPUT_FILE)
    if not INPUT_FILE.exists():
        # Kiểm tra xem có file Word cùng tên không nếu không thấy Excel
        WORD_INPUT = INPUT_FILE.with_suffix('.docx')
        if WORD_INPUT.exists():
            INPUT_FILE = WORD_INPUT
        else:
            print(f"❌ Lỗi: Không tìm thấy file đầu vào (.xlsx hoặc .docx) tại:\n{INPUT_FILE.parent}")
            return
                
    print(f"📖 Đang đọc danh sách thẩm định: {INPUT_FILE.name}")
    try:
        # Gọi hàm đọc linh hoạt đã viết ở trên
        df_input = read_input_file(INPUT_FILE)
        print(f"✅ Đã nạp {len(df_input)} dòng từ {INPUT_FILE.name}")
        
        # 4. CHẠY THẨM ĐỊNH (Giữ nguyên logic cũ)
        print(f"🔍 AI đang đối chiếu dữ liệu...")
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