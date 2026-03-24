import os
import sys
import time
from pathlib import Path

# Fix đường dẫn để import được pipeline
current_file = Path(__file__).resolve()
project_root = current_file.parent 
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pipeline import MaterialAuditPipeline
except ImportError as e:
    print(f"❌ Lỗi Import: {e}. Kiểm tra lại file pipeline.py")
    sys.exit(1)

def run_initialization():
    # --- CẤU HÌNH ĐƯỜNG DẪN ---
    # File ERP Master (Dữ liệu gốc từ Meili/Excel)
    ERP_MASTER_FILE = project_root / "data" / "raw" / "Data_For_Meili.xlsx"
    
    # Nơi lưu kết quả sau khi AI "học" xong
    INDEX_SAVE_PATH = project_root / "data" / "processed" / "faiss.index"
    META_SAVE_PATH = project_root / "data" / "processed" / "faiss_meta.json"
    CONFIG_DIR = project_root / "config"

    # Tạo thư mục processed nếu chưa có
    os.makedirs(project_root / "data" / "processed", exist_ok=True)

    print("="*60)
    print("🚀 HỆ THỐNG KHỞI TẠO CHỈ MỤC AI (AI INDEX INITIALIZER)")
    print("="*60)
    
    if not ERP_MASTER_FILE.exists():
        print(f"❌ Lỗi: Không tìm thấy file dữ liệu gốc tại:\n{ERP_MASTER_FILE}")
        return

    start_time = time.time()

    try:
        # 1. Khởi tạo Pipeline
        print(f"⚙️  Đang nạp mô hình AI (BGE-M3)... Vui lòng đợi...")
        pipe = MaterialAuditPipeline(config_path=str(CONFIG_DIR))

        # 2. Chạy bước Build Index
        # Hàm build_index trong pipeline đã có sẵn tqdm để hiện thanh tiến trình
        print(f"📦 Bắt đầu xử lý file: {ERP_MASTER_FILE.name}")
        pipe.build_index(
            erp_file=str(ERP_MASTER_FILE),
            index_path=str(INDEX_SAVE_PATH),
            metadata_path=str(META_SAVE_PATH)
        )

        end_time = time.time()
        duration = round((end_time - start_time) / 60, 2)

        print("\n" + "="*60)
        print(f"✅ KHỞI TẠO THÀNH CÔNG!")
        print(f"⏱️  Tổng thời gian xử lý: {duration} phút")
        print(f"💾 File Index: {INDEX_SAVE_PATH.name}")
        print(f"💾 File Metadata: {META_SAVE_PATH.name}")
        print("👉 Bây giờ bạn có thể chạy file Test Recall hoặc App chính.")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI TRONG QUÁ TRÌNH KHỞI TẠO:")
        print(f"👉 {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_initialization()