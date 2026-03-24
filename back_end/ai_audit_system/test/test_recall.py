import os
import sys
from pathlib import Path

# --- CẤU HÌNH ĐƯỜNG DẪN ĐỂ IMPORT PIPELINE ---
# Lấy đường dẫn đến thư mục ai_audit_system (thư mục cha của thư mục test)
current_file = Path(__file__).resolve()
project_root = current_file.parents[1] 

# Thêm project_root vào hệ thống để có thể 'from pipeline import ...'
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pipeline import MaterialAuditPipeline
    print("✅ Đã kết nối với Pipeline thành công.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}. Hãy kiểm tra file pipeline.py có nằm ở: {project_root}")
    sys.exit(1)

def test_load_colab_data():
    # --- CẤU HÌNH ĐƯỜNG DẪN DỮ LIỆU ---
    # Trỏ đúng vào thư mục data/processed từ Colab tải về
    INDEX_PATH = project_root / "data" / "processed" / "faiss.index"
    META_PATH  = project_root / "data" / "processed" / "faiss_meta.json"
    CONFIG_DIR = project_root / "config"

    print("\n" + "="*50)
    print("🚀 ĐANG KIỂM TRA FILE INDEX TỪ COLAB")
    print("="*50)

    # 1. Kiểm tra file vật lý
    if not INDEX_PATH.exists():
        print(f"❌ KHÔNG TÌM THẤY file index tại: {INDEX_PATH}")
        return
    if not META_PATH.exists():
        print(f"❌ KHÔNG TÌM THẤY file metadata tại: {META_PATH}")
        return

    try:
        # 2. Khởi tạo Pipeline & Load Index
        # (Lưu ý: MaterialAuditPipeline phải có hàm load_index)
        pipe = MaterialAuditPipeline(config_path=str(CONFIG_DIR))
        
        print(f"⚙️  Đang nạp file index ({INDEX_PATH.name})...")
        pipe.load_index(str(INDEX_PATH), str(META_PATH))

        # 3. Kiểm tra dữ liệu nạp vào
        # Giả sử metadata được lưu trong biến pipe.metadata
        if hasattr(pipe, 'metadata'):
            count = len(pipe.metadata)
            print(f"✅ Nạp data thành công! Tổng số vật tư: {count} dòng.")
            
            if count == 20015:
                print("🎯 Số lượng dòng khớp hoàn toàn với dữ liệu Colab!")
            else:
                print(f"⚠️ Số lượng dòng ({count}) khác với dự kiến (20015).")
        
        # 4. Chạy thử 1 câu Search thực tế
        print("\n🔎 Chạy thử tìm kiếm mẫu:")
        query = "Van cửa DN100"
        # Giả sử hàm search trả về list các dictionary
        results = pipe.search(query, top_k=3)
        
        if results:
            print("\n🔎 Kiểm tra cấu trúc thực tế của 1 kết quả:")
            first_res = results[0]
            print(f"--- Các khóa (Keys) tìm thấy: {list(first_res.keys())} ---")
            
            print("\n🔎 Chi tiết kết quả:")
            for i, item in enumerate(results):
                # Dùng vòng lặp in ra toàn bộ để không bị sót
                print(f"   [{i+1}]", end=" ")
                for key, value in item.items():
                    print(f"{key}: {value} |", end=" ")
                print("\n" + "-"*30)

    except Exception as e:
        print(f"❌ Lỗi khi thực thi: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load_colab_data()