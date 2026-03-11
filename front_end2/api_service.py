import requests

API_BASE = "http://localhost:8000"

def get_system_status():
    try:
        return requests.get(f"{API_BASE}/system-status", timeout=5).json()
    except:
        return {"status": "error", "message": "Không thể kết nối đến Backend (Kiểm tra server)"}

def search_query(text):
    # Khớp với Form(...) trong Backend
    try:
        response = requests.post(f"{API_BASE}/search", data={"query": text})
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def upload_database(file_bytes, file_name, password):
    # Khớp với File(...) và Form(...) trong Backend
    try:
        files = {"file": (file_name, file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"password": password}
        response = requests.post(f"{API_BASE}/admin/upload-excel", files=files, data=data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_build_progress():
    try:
        return requests.get(f"{API_BASE}/admin/progress").json()
    except:
        return {"percent": 0, "task": "Lỗi kết nối..."}