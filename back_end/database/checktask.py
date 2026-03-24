import meilisearch

# Kết nối
url = "http://127.0.0.1:7700"
key = "HieuVinhTan4_2026"
client = meilisearch.Client(url, key)

def check():
    print("🔍 Đang kiểm tra tiến độ xử lý dữ liệu...")
    
    # Lấy danh sách các tác vụ (Dùng dấu chấm để truy cập thuộc tính)
    tasks = client.get_tasks()
    
    # Ở bản mới, tasks là một object có thuộc tính .results
    for task in tasks.results:
        status = task.status
        task_type = task.type
        print(f"📌 Task UID {task.uid}: Loại [{task_type}] - Trạng thái: [{status}]")
        
        if status == 'failed':
            # Truy cập lỗi nếu có
            print(f"❌ Chi tiết lỗi: {task.error}")

    print("-" * 40)
    # Kiểm tra số lượng thực tế trong index
    try:
        index = client.index('vattu_vintan4')
        stats = index.get_stats()
        # Dùng stats.number_of_documents ở bản mới
        print(f"📊 Tổng số món vật tư hiện có trong kho: {stats.number_of_documents}")
    except Exception as e:
        print(f"⚠️ Chưa thấy index: {e}")

if __name__ == "__main__":
    check()