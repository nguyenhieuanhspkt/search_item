import os
import sys
import time

# --- 1. THIẾT LẬP ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

print("="*50)
print("   KIỂM TRA TRẠNG THÁI NẠP AI LEGACY (BGE-M3)")
print("="*50)

# --- 2. KIỂM TRA FILE VẬT LÝ ---
def check_paths():
    paths = {
        "Thư mục Core 1 (Legacy)": os.path.join(BASE_DIR, "core"),
        "Thư mục AI Models (BGE)": os.path.join(BASE_DIR, "AI_models", "BGE"),
        "Dữ liệu Index (vattu_index)": os.path.join(BASE_DIR, "vattu_index"),
        "Cơ sở dữ liệu Core 2 (SQLite)": os.path.join(BASE_DIR, "core2", "entities.db")
    }
    
    all_ok = True
    for name, path in paths.items():
        if os.path.exists(path):
            print(f"✅ [FOUND] {name}")
        else:
            print(f"❌ [MISSING] {name}\n   --> Đường dẫn: {path}")
            all_ok = False
    return all_ok

# --- 3. THỬ IMPORT VÀ LOAD MODEL ---
def try_load_legacy():
    print("\n--- Đang thử nạp Model AI vào RAM (Vui lòng đợi)... ---")
    start_time = time.time()
    try:
        # Thử import
        from core.engine import HybridSearchEngine
        
        # Thử khởi tạo (Đây là bước nặng nhất)
        MODEL_PATH = os.path.join(BASE_DIR, "AI_models", "BGE")
        INDEX_DIR = os.path.join(BASE_DIR, "vattu_index")
        
        test_engine = HybridSearchEngine(model_path=MODEL_PATH, index_dir=INDEX_DIR)
        
        end_time = time.time()
        print(f"✅ [SUCCESS] AI Legacy đã nạp thành công trong {round(end_time - start_time, 2)} giây!")
        return True
    except ImportError as e:
        print(f"❌ [FAILED] Không thể Import: {e}")
        print("   --> Kiểm tra lại tên thư mục 'core' và file 'engine.py'")
    except Exception as e:
        print(f"❌ [ERROR] Lỗi khi load Model: {e}")
        print("   --> Có thể thiếu thư viện: pip install sentence-transformers whoosh")
    return False

if __name__ == "__main__":
    path_ok = check_paths()
    if path_ok:
        load_ok = try_load_legacy()
        if load_ok:
            print("\n🚀 KẾT LUẬN: Hệ thống AI Legacy của Hiếu đã sẵn sàng 100%!")
        else:
            print("\n⚠️ KẾT LUẬN: File có đủ nhưng Model không chạy được.")
    else:
        print("\n❌ KẾT LUẬN: Thiếu file/thư mục. AI không thể khởi động.")
    print("="*50)