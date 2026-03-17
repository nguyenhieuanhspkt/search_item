from fastapi import FastAPI, Form, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
import pandas as pd
import shutil
import io
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from .core.engine import HybridSearchEngine 
from .core.bulk_processor import BulkMatcher
from pydantic import BaseModel
from typing import List, Optional
app = FastAPI()

# --- 1. CẤU HÌNH ---
ADMIN_PASSWORD = "admin123"
INDEX_DIR = "vattu_index"
MODEL_PATH = 'keepitreal/vietnamese-sbert'

# Biến toàn cục
engine = None
bulk_matcher = None # Thêm biến này
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

# --- 3. SỰ KIỆN STARTUP ---
@app.on_event("startup")
async def load_ai():
    global engine, bulk_matcher, is_model_loaded
    print("--- Đang khởi động hệ thống AI... ---")
    
    def init():
        # Ưu tiên load model local BGE nếu có
        path = MODEL_PATH if os.path.exists(MODEL_PATH) else 'keepitreal/vietnamese-sbert'
        eg = HybridSearchEngine(path, INDEX_DIR)
        bm = BulkMatcher(eg) # Khởi tạo luôn BulkMatcher dùng chung engine
        return eg, bm
    
    # Nạp model ngầm để không chặn startup
    loop = asyncio.get_event_loop()
    # Chạy init trong executor để không block server startup
    engine, bulk_matcher = await loop.run_in_executor(None, init)
    is_model_loaded = True
    print(f"--- Hệ thống AI ({MODEL_PATH}) đã sẵn sàng! ---")

# --- 4. LOGIC XỬ LÝ INDEX (CHẠY NGẦM) ---
def sync_build_index(df: pd.DataFrame):
    global current_progress, engine
    try:
        current_progress = {"percent": 5, "task": "Đang làm sạch thư mục cũ..."}
        
        if os.path.exists(INDEX_DIR):
            shutil.rmtree(INDEX_DIR)
        os.makedirs(INDEX_DIR)

        # Định nghĩa Schema khớp với Engine
        schema = Schema(
            ma_vattu=ID(stored=True),
            ten_vattu=TEXT(stored=True),
            thong_so=TEXT(stored=True),
            hang_sx=TEXT(stored=True),
            dvt=TEXT(stored=True),
            note=TEXT(stored=True),
            all_text=TEXT(stored=True)
        )

        ix = create_in(INDEX_DIR, schema)
        writer = ix.writer()
        df = df.fillna("")
        total_rows = len(df)

        def clean(v):
            v_str = str(v).strip()
            if v_str.lower() in ['nan', 'none', 'n/a', '']:
                return ""
            return v_str

        for i, row in df.iterrows():
            # Cập nhật tiến độ sau mỗi 50 dòng để tiết kiệm tài nguyên
            if i % 50 == 0 or i == total_rows - 1:
                percent = int((i / total_rows) * 80) + 10
                current_progress = {"percent": percent, "task": f"Đang nạp dữ liệu: {i}/{total_rows}"}

            # Map chính xác theo file Excel của bạn
            ma = clean(row.get('Mã vật tư', ''))
            ten = clean(row.get('Tên vật tư', ''))
            ts = clean(row.get('Mã hiệu/Thông số kỹ thuật', ''))
            hang = clean(row.get('Hãng sản xuất', ''))
            dvt = clean(row.get('ĐVT', ''))
            note = clean(row.get('Ghi chú', '')) # Ghi chú chứa note

            # Gom text để AI tìm kiếm
            full_info = f"{ma} {ten} {ts} {hang} {note}"
            
            writer.add_document(
                ma_vattu=ma,
                ten_vattu=ten,
                thong_so=ts,
                hang_sx=hang,
                dvt=dvt if dvt else "Cái",
                note=note,
                all_text=full_info
            )
        
        current_progress = {"percent": 90, "task": "Đang tối ưu hóa tìm kiếm..."}
        writer.commit()
        global bulk_matcher
        engine = HybridSearchEngine(MODEL_PATH, INDEX_DIR)
        bulk_matcher = BulkMatcher(engine) # Cập nhật cả bulk_matcher khi index thay đổi
         
        current_progress = {"percent": 100, "task": "Hoàn tất"}
        
    except Exception as e:
        print(f"Lỗi build index: {e}")
        current_progress = {"percent": 0, "task": f"Lỗi: {str(e)}"}

# --- 5. HỆ THỐNG API ---

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
        return {"error": "Hệ thống chưa sẵn sàng hoặc chưa có dữ liệu"}
    
    # Gọi engine search đã được tối ưu
    results = engine.search(query, top_k=5)
    
    # Trả về JSON sạch cho Frontend
    return [
        {
            "ma": r.get('ma', ''),
            "ten": r.get('ten', ''),
            "ts": r.get('ts', ''),
            "hang": r.get('hang', ''), # Đã đồng bộ key 'hang' với engine
            "dvt": r.get('dvt', 'N/A'),
            "note": r.get('note', ''),
            "final_score": float(r.get('final_score', 0)),
            "ai_relevance": float(r.get('ai_relevance', 0))
        } for r in results
    ]

@app.post("/admin/upload-excel")
async def upload_excel(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    password: str = Form(...)
):
    if password != ADMIN_PASSWORD:
        return {"error": "Sai mật mã quản trị viên!"}
    
    global current_progress
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        current_progress = {"percent": 0, "task": "Bắt đầu nạp file..."}
        background_tasks.add_task(sync_build_index, df)
        return {"message": "Đang xử lý ngầm, vui lòng theo dõi tiến trình."}
    except Exception as e:
        return {"error": f"Lỗi đọc file: {str(e)}"}

@app.get("/admin/progress")
async def get_progress():
    return current_progress

engine = HybridSearchEngine()
bulk_matcher = BulkMatcher(engine)
class MaterialInput(BaseModel):
    stt: Optional[str] = None
    ten: str
    tskt: Optional[str] = ""
    dvt: Optional[str] = ""
# 2. Sửa lại API nhận dữ liệu
@app.post("/api/bulk-match")
async def handle_bulk_match(items: List[MaterialInput]): # <--- Dùng List[MaterialInput] thay vì list
    if not is_model_loaded or bulk_matcher is None:
        return {"status": "error", "message": "Hệ thống AI đang khởi động..."}
    
    try:
        # Chuyển đổi List Pydantic sang List Dict để bulk_matcher xử lý
        input_data = [item.dict() for item in items]
        results = bulk_matcher.process_data(input_data)
        return {
            "status": "success",
            "total": len(results),
            "data": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    
from fastapi import UploadFile, File
from docx import Document
import io

@app.post("/extract-word")
async def extract_word(file: UploadFile = File(...)):
    contents = await file.read()
    doc = Document(io.BytesIO(contents))
    data = []
    
    for table in doc.tables:
        for row in table.rows[1:]: # Bỏ qua header
            cells = row.cells
            if len(cells) >= 4:
                data.append({
                    "stt": cells[0].text.strip(),
                    "ten": cells[1].text.strip(),
                    "ts": cells[2].text.strip(),
                    "dvt_word": cells[3].text.strip()
                })
    return data