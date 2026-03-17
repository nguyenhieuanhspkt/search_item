from fastapi import FastAPI, Form, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import pandas as pd
import shutil
import io
from docx import Document
from typing import List, Optional
from pydantic import BaseModel

# Giả định các module này bạn đã có sẵn trong thư mục core
# from .core.engine import HybridSearchEngine 
# from .core.bulk_processor import BulkMatcher

app = FastAPI()

# --- 1. CẤU HÌNH ---
ADMIN_PASSWORD = "admin123"
INDEX_DIR = "vattu_index"
MODEL_PATH = 'keepitreal/vietnamese-sbert'

# Biến toàn cục
engine = None
bulk_matcher = None
is_model_loaded = False
current_progress = {"percent": 0, "task": "Idle"}

# --- 2. MIDDLEWARE (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. MODEL DỮ LIỆU ---
class MaterialInput(BaseModel):
    stt: Optional[str] = None
    ten: str
    tskt: Optional[str] = ""
    dvt: Optional[str] = ""

# --- 4. ENDPOINT: TRÍCH XUẤT FILE WORD (Dùng cho Preview) ---
@app.post("/extract-word")
async def extract_word(file: UploadFile = File(...)):
    """
    Nhận file .docx, trả về danh sách JSON các dòng trong bảng.
    Dùng để hiển thị Preview trên React Frontend.
    """
    try:
        contents = await file.read()
        doc = Document(io.BytesIO(contents))
        data = []
        
        for table in doc.tables:
            # Duyệt từ dòng thứ 2 (bỏ qua header)
            for row in table.rows[1:]:
                cells = row.cells
                # Kiểm tra nếu dòng có ít nhất 2 cột (STT và Tên) và không rỗng
                if len(cells) >= 2:
                    ten_vt = cells[1].text.strip()
                    if ten_vt:  # Chỉ lấy nếu có tên vật tư
                        data.append({
                            "stt": cells[0].text.strip(),
                            "ten": ten_vt,
                            "ts": cells[2].text.strip() if len(cells) > 2 else "",
                            "dvt_word": cells[3].text.strip() if len(cells) > 3 else ""
                        })
        return data
    except Exception as e:
        return {"error": f"Không thể đọc file Word: {str(e)}"}

# --- 5. ENDPOINT: THẨM ĐỊNH HÀNG LOẠT ---
@app.post("/api/bulk-match")
async def handle_bulk_match(items: List[MaterialInput]):
    if not is_model_loaded or bulk_matcher is None:
        return {"status": "error", "message": "Hệ thống AI đang khởi động..."}
    
    try:
        input_data = [item.dict() for item in items]
        results = bulk_matcher.process_data(input_data)
        return {
            "status": "success",
            "total": len(results),
            "data": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 6. CÁC API HỆ THỐNG KHÁC ---

@app.get("/system-status")
async def get_status():
    if not is_model_loaded:
        return {"status": "loading", "message": "Đang tải Model AI..."}
    if os.path.exists(INDEX_DIR) and len(os.listdir(INDEX_DIR)) > 0:
        return {"status": "ready", "message": "Hệ thống đã sẵn sàng"}
    return {"status": "warning", "message": "Hệ thống chưa có dữ liệu Index"}

@app.post("/search")
async def search_api(query: str = Form(...)):
    if not is_model_loaded or engine is None:
        return {"error": "Hệ thống chưa sẵn sàng"}
    results = engine.search(query, top_k=5)
    return [
        {
            "ma": r.get('ma', ''),
            "ten": r.get('ten', ''),
            "ts": r.get('ts', ''),
            "hang": r.get('hang', ''),
            "dvt": r.get('dvt', 'N/A'),
            "final_score": float(r.get('final_score', 0))
        } for r in results
    ]

# --- 7. SỰ KIỆN KHỞI ĐỘNG (STARTUP) ---
@app.on_event("startup")
async def load_ai():
    global engine, bulk_matcher, is_model_loaded
    # Lưu ý: Bạn cần import HybridSearchEngine và BulkMatcher ở đây
    # Giả lập load model
    await asyncio.sleep(1) 
    is_model_loaded = True
    print("--- Hệ thống AI đã sẵn sàng! ---")