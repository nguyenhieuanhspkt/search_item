from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import shutil
import io
import asyncio
import pandas as pd
from docx import Document
from typing import List, Optional
from pydantic import BaseModel

# --- 1. SETUP ĐƯỜNG DẪN VÀ IMPORT ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from core.engine import HybridSearchEngine 
    from core.bulk_processor import BulkMatcher
except ImportError as e:
    print(f"⚠️ Lỗi nghiêm trọng: Không tìm thấy thư mục core hoặc thiếu file: {e}")
    HybridSearchEngine = None
    BulkMatcher = None

app = FastAPI(title="Hệ thống Thẩm định Vật tư v2.6")

# --- 2. CẤU HÌNH HỆ THỐNG ---
INDEX_DIR = os.path.join(BASE_DIR, "vattu_index")
ADMIN_PASSWORD = "admin123"

# Khởi tạo biến toàn cục
engine = None
bulk_matcher = None
is_model_loaded = False

# Cấu hình CORS cho React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model dữ liệu đầu vào từ React
class MaterialInput(BaseModel):
    stt: Optional[str] = None
    ten: str
    tskt: Optional[str] = ""
    dvt: Optional[str] = ""

# --- 3. SỰ KIỆN KHỞI ĐỘNG (STARTUP) ---
@app.on_event("startup")
async def load_ai():
    global engine, bulk_matcher, is_model_loaded
    try:
        if HybridSearchEngine:
            # Khởi tạo engine ngay lập tức (Engine sẽ tự tìm BGE hoặc SBERT)
            engine = HybridSearchEngine(index_dir=INDEX_DIR)
            
            # Kiểm tra nếu đã có dữ liệu index cũ thì nạp Matcher luôn
            if os.path.exists(INDEX_DIR) and len(os.listdir(INDEX_DIR)) > 0:
                bulk_matcher = BulkMatcher(engine=engine)
                print(f"--- ✅ AI Sẵn sàng. Model đang dùng: {engine.current_model_name_or_path} ---")
            else:
                print("--- ⚠️ Hệ thống chưa có dữ liệu Index. Chờ nạp Excel... ---")
            
            is_model_loaded = True
    except Exception as e:
        print(f"--- ❌ LỖI KHỞI ĐỘNG HỆ THỐNG: {str(e)} ---")

# --- 4. ENDPOINT: QUẢN TRỊ & NẠP DỮ LIỆU ---
@app.post("/admin/rebuild-index")
async def rebuild_index(file: UploadFile = File(...), password: str = Form(...)):
    global engine, bulk_matcher
    if password != ADMIN_PASSWORD:
        return {"status": "error", "message": "Sai mật khẩu Admin"}
    
    temp_path = os.path.join(BASE_DIR, "temp_data.xlsx")
    try:
        # 1. Lưu file tạm
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Làm sạch thư mục Index
        if os.path.exists(INDEX_DIR):
            shutil.rmtree(INDEX_DIR)
        os.makedirs(INDEX_DIR)
        
        # 3. Thực hiện xây dựng Index (Ghi file xuống đĩa)
        print(f"--- Đang xây dựng Index từ file: {file.filename} ---")
        
        # Đảm bảo engine đã tồn tại
        if engine is None:
            engine = HybridSearchEngine(index_dir=INDEX_DIR)
            
        success = engine.build_and_save_index(temp_path, INDEX_DIR)
        
        if success:
            # QUAN TRỌNG: Re-init để Engine nạp lại các file Index vừa tạo
            engine.__init__(index_dir=INDEX_DIR)
            bulk_matcher = BulkMatcher(engine=engine)
            
            # Xóa file Excel tạm sau khi nạp xong
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return {
                "status": "success", 
                "message": f"Nạp dữ liệu thành công bằng {engine.current_model_name_or_path}"
            }
        else:
            return {"status": "error", "message": "Lỗi xử lý file Excel. Kiểm tra lại định dạng cột."}

    except Exception as e:
        print(f"❌ Lỗi Rebuild: {str(e)}")
        return {"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}

# --- 5. ENDPOINT: TRẠNG THÁI & TÌM KIẾM ---
@app.get("/system-status")
async def get_status():
    if not is_model_loaded:
        return {"status": "loading", "message": "Đang nạp Model AI..."}
    
    # Kiểm tra xem folder index có file thực tế chưa
    has_index = os.path.exists(INDEX_DIR) and len([f for f in os.listdir(INDEX_DIR) if not f.startswith('.')]) > 0
    
    if not has_index:
        return {"status": "warning", "message": "Chưa có dữ liệu Index"}
        
    return {"status": "ready", "message": f"Sẵn sàng ({engine.current_model_name_or_path})"}

@app.post("/search")
async def search_api(query: str = Form(...)):
    if not is_model_loaded or engine is None:
        return {"error": "Hệ thống chưa sẵn sàng."}
    
    try:
        query_str = query.strip()
        if not query_str: return []

        # Gọi hàm search lai ghép
        results = engine.search(query_str, top_k=5)
        
        # Map kết quả khớp với giao diện React
        return [{
            "erp": r.get('ma_vattu') or r.get('ma') or '---',
            "ten": r.get('ten_vattu') or r.get('ten', 'Không tên'),
            "ts": r.get('thong_so') or r.get('ts', ''),
            "hang": r.get('hang_sx') or r.get('hang', ''),
            "dvt": r.get('dvt', 'N/A'),
            "final_score": round(float(r.get('final_score', 0)), 2)
        } for r in results]
    except Exception as e:
        return {"error": f"Lỗi tìm kiếm: {str(e)}"}

# --- 6. ENDPOINT: XỬ LÝ FILE WORD & THẨM ĐỊNH HÀNG LOẠT ---
@app.post("/extract-word")
async def extract_word(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        doc = Document(io.BytesIO(contents))
        data = []
        for table in doc.tables:
            for row in table.rows[1:]: # Bỏ qua dòng tiêu đề bảng
                cells = row.cells
                if len(cells) >= 2:
                    ten_vt = cells[1].text.strip()
                    if ten_vt:
                        data.append({
                            "stt": cells[0].text.strip(),
                            "ten": ten_vt,
                            "ts": cells[2].text.strip() if len(cells) > 2 else "",
                            "dvt_word": cells[3].text.strip() if len(cells) > 3 else ""
                        })
        return data
    except Exception as e:
        return {"error": f"Lỗi đọc file Word: {str(e)}"}

@app.post("/api/bulk-match")
async def handle_bulk_match(items: List[MaterialInput]):
    if not is_model_loaded or bulk_matcher is None:
        return {"status": "error", "message": "AI chưa sẵn sàng hoặc chưa nạp Index."}
    
    try:
        input_data = [item.dict() for item in items]
        results = bulk_matcher.process_data(input_data)
        return {"status": "success", "total": len(results), "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
base_path = os.path.dirname(os.path.abspath(__file__))
dist_path = os.path.join(os.path.dirname(base_path), "front_end", "dist")

if os.path.exists(dist_path):
    # Mount thư mục dist để truy cập file static (css, js, img)
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    # Route mặc định trả về file index.html của React
    @app.get("/")
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str = None):
        return FileResponse(os.path.join(dist_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)