import time
import pandas as pd
import meilisearch
import os
import socket
import numpy as np

def get_paths():
    hostname = socket.gethostname()
    path_coquan = r"D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end"
    path_onha = r"D:\TaskApp_pro\search_item\back_end"
    base = path_coquan if os.path.exists(path_coquan) else path_onha
    return {
        "excel": os.path.join(base, "Data_For_Meili.xlsx"),
        "url": "http://127.0.0.1:7700",
        "key": "HieuVinhTan4_2026"
    }

def push_to_meili():
    config = get_paths()
    client = meilisearch.Client(config["url"], config["key"])

    if not os.path.exists(config["excel"]):
        print(f"❌ Không thấy file: {config['excel']}")
        return

    # --- BƯỚC 1: XÓA INDEX CŨ VÀ ĐỢI XÁC NHẬN ---
    print("🗑 Đang tiến hành làm sạch kho cũ 'vattu_vintan4'...")
    try:
        # Gửi lệnh xóa và lấy task_uid
        task = client.index('vattu_vintan4').delete()
        print(f"⏳ Đang chờ Meilisearch xóa hoàn tất (Task ID: {task.task_uid})...")
        
        # Đợi cho đến khi task xóa báo 'succeeded'
        while True:
            status = client.get_task(task.task_uid)
            if status.status == 'succeeded':
                print("✅ Đã xóa trắng kho cũ thành công!")
                break
            elif status.status == 'failed':
                print("⚠️ Lỗi khi xóa index, có thể index không tồn tại.")
                break
            time.sleep(0.5) # Nghỉ nửa giây rồi check tiếp
    except Exception as e:
        print(f"ℹ️ Thông báo: Không tìm thấy index cũ để xóa hoặc có lỗi nhẹ: {e}")

    # --- BƯỚC 2: ĐỌC VÀ CHUẨN HÓA DỮ LIỆU ---
    print(f"📂 Đang đọc dữ liệu từ: {config['excel']}")
    df = pd.read_excel(config["excel"])
    df = df.replace({np.nan: None}) 

    print("🛠 Đang chuẩn hóa ID (thay dấu chấm bằng gạch dưới)...")
    # Đảm bảo 'Mã vật tư' là string trước khi replace
    df['id_meili'] = df['Mã vật tư'].astype(str).str.replace('.', '_', regex=False)

    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            df[col] = df[col].astype(str)

    documents = df.to_dict(orient='records')
    total = len(documents)
    
    # --- BƯỚC 3: NẠP DỮ LIỆU MỚI ---
    index = client.index('vattu_vintan4')
    chunk_size = 2000
    for i in range(0, total, chunk_size):
        chunk = documents[i:i + chunk_size]
        # Ép primary_key là 'id_meili' để tránh lỗi dấu chấm
        index.add_documents(chunk, primary_key='id_meili')
        print(f"🚀 Đang nạp đợt {i//chunk_size + 1}: {min(i+chunk_size, total)}/{total} dòng.")

    print(f"\n🎉 HOÀN TẤT! Dữ liệu đã sạch và mới 100%.")
    print(f"🔗 Kiểm tra tại: {config['url']}")

if __name__ == "__main__":
    push_to_meili()