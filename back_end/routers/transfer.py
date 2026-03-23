import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter()

# ĐƯỜNG DẪN ĐÍCH CHÍNH XÁC CỦA HIẾU
# Lưu ý: Chữ r đứng trước dấu ngoặc kép là BẮT BUỘC để xử lý các dấu gạch chéo ngược \
TARGET_DIR = r"D:\onedrive_hieuna\OneDrive - EVN\Tổ Thẩm định\Năm 2026\Thẩm định 98_hieuna_3"

@router.post("/colleague/upload", tags=["Transfer"])
async def upload_to_specific_folder(files: List[UploadFile] = File(...)):
    # 1. Kiểm tra xem thư mục đích có tồn tại không
    if not os.path.exists(TARGET_DIR):
        try:
            os.makedirs(TARGET_DIR, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Không thể tạo hoặc truy cập thư mục: {str(e)}"
            )

    saved_info = []
    
    try:
        for file in files:
            # Làm sạch tên file để tránh lỗi hệ thống
            safe_name = os.path.basename(file.filename)
            final_path = os.path.join(TARGET_DIR, safe_name)
            
            # Ghi file theo kiểu stream để cân file 900MB
            with open(final_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            saved_info.append(safe_name)
            
        return {
            "status": "success",
            "message": f"Đã nhận {len(saved_info)} file vào thư mục Thẩm định 98",
            "folder": TARGET_DIR,
            "files": saved_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi ghi file: {str(e)}")
    
@router.get("/colleague/files", tags=["Transfer"])
async def get_uploaded_files():
    try:
        if not os.path.exists(TARGET_DIR):
            return []
        
        files = []
        for filename in os.listdir(TARGET_DIR):
            path = os.path.join(TARGET_DIR, filename)
            if os.path.isfile(path):
                stats = os.stat(path)
                files.append({
                    "name": filename,
                    "size": round(stats.st_size / (1024 * 1024), 2),
                    "time": stats.st_mtime
                })
        
        # Sắp xếp file mới nhất lên đầu để đồng nghiệp dễ thấy
        files.sort(key=lambda x: x['time'], reverse=True)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))