import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from typing import List

router = APIRouter()

# ĐỊNH NGHĨA ĐƯỜNG DẪN GỐC (Chỉ đến thư mục Năm 2026)
BASE_PATH = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026"

@router.post("/colleague/upload", tags=["Transfer"])
async def upload_to_specific_folder(
    folder: str = Form(...),  # Nhận tên thư mục động từ React gửi lên
    files: List[UploadFile] = File(...)
):
    """Xử lý nhận file và lưu vào đúng thư mục hồ sơ đang chọn"""
    
    # 1. Tạo đường dẫn đích dựa trên folder được truyền từ Link Zalo
    target_dir = os.path.join(BASE_PATH, folder)
    
    # 2. Kiểm tra và tạo thư mục nếu chưa có
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Không thể tạo thư mục trên máy Hiếu: {str(e)}"
            )

    saved_info = []
    try:
        for file in files:
            safe_name = os.path.basename(file.filename)
            final_path = os.path.join(target_dir, safe_name)
            
            # Ghi file theo kiểu stream để hỗ trợ file nặng
            with open(final_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            saved_info.append(safe_name)
            
        return {
            "status": "success",
            "message": f"Đã nhận {len(saved_info)} file vào đúng thư mục: {folder}",
            "folder": folder,
            "files": saved_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi ghi file vào ổ cứng: {str(e)}")

@router.get("/colleague/files", tags=["Transfer"])
async def get_uploaded_files(
    folder: str = Query(...) # Nhận folder để biết phải lấy danh sách file ở đâu
):
    """Lấy danh sách file trong đúng thư mục đang làm việc để hiển thị lên Web"""
    try:
        target_dir = os.path.join(BASE_PATH, folder)
        
        if not os.path.exists(target_dir):
            return []
        
        files_list = []
        for filename in os.listdir(target_dir):
            path = os.path.join(target_dir, filename)
            if os.path.isfile(path):
                stats = os.stat(path)
                files_list.append({
                    "name": filename,
                    "size": round(stats.st_size / (1024 * 1024), 2),
                    "time": stats.st_mtime
                })
        
        # Sắp xếp file mới nhất lên đầu
        files_list.sort(key=lambda x: x['time'], reverse=True)
        return files_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi quét thư mục: {str(e)}")