from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import shutil
import io
import json
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
# Tìm đường dẫn model local
MODEL_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "AI_models", "BGE")
ADMIN_PASSWORD = "admin123"

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
    stt: str = ""
    ten: str = ""   # Phải khớp với 'ten' trong payload
    tskt: str = ""  # Phải khớp với 'tskt' trong payload
    dvt: str = ""


# --- 3. SỰ KIỆN KHỞI ĐỘNG (STARTUP) ---
@app.on_event("startup")
async def load_ai():
    global engine, bulk_matcher, is_model_loaded
    try:
        if HybridSearchEngine:
            # SỬA TẠI ĐÂY: Khởi tạo theo đúng tham số của engine.py mới
            engine = HybridSearchEngine(model_path=MODEL_PATH, index_dir=INDEX_DIR)
            
            # Kiểm tra dữ liệu index
            if os.path.exists(INDEX_DIR) and any(os.listdir(INDEX_DIR)):
                if BulkMatcher:
                    bulk_matcher = BulkMatcher(engine=engine)
                # SỬA TẠI ĐÂY: Lấy tên model từ scorers
                model_name = engine.scorers.bi.model.get_parameter("embeddings.word_embeddings.weight").shape if hasattr(engine.scorers.bi.model, "model_card") else "BGE-M3"
                print(f"--- ✅ AI Sẵn sàng ---")
            
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
    
    # Ghi file tạm đồng bộ vì đây là bước khởi đầu nhanh
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    def progress_stream():
        # Gọi hàm generator từ engine (Giữ nguyên tên hàm)
        for step in engine.build_and_save_index(temp_path, overwrite=True):
            # Trả về định dạng Server-Sent Events (SSE)
            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
        
        # Sau khi xong hết thì xử lý hậu kỳ
        try:
            # Re-init BulkMatcher nếu cần
            # Lưu ý: BulkMatcher nên được init lại sau khi stream thành công ở bước cuối
            if BulkMatcher:
                globals()['bulk_matcher'] = BulkMatcher(engine=engine)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass

    return StreamingResponse(progress_stream(), media_type="text/event-stream")

# --- 5. ENDPOINT: TRẠNG THÁI & TÌM KIẾM ---
@app.get("/system-status")
async def get_status():
    if not is_model_loaded:
        return {"status": "loading", "message": "Đang nạp Model AI..."}
    
    has_index = os.path.exists(INDEX_DIR) and any(os.listdir(INDEX_DIR))
    if not has_index:
        return {"status": "warning", "message": "Chưa có dữ liệu Index"}
        
    # SỬA TẠI ĐÂY: Trả về tên model từ config hoặc scorers
    return {"status": "ready", "message": f"Sẵn sàng (BGE-M3 Local)"}

@app.post("/search")
async def search_api(query: str = Form(...)):
    if not is_model_loaded or engine is None:
        return {"error": "Hệ thống chưa sẵn sàng."}
    
    try:
        query_str = query.strip()
        if not query_str: return []

        # SỬA TẠI ĐÂY: Map lại key theo cấu hình Dictionary mới của engine.py
        results = engine.search(query_str, top_k=5, explain=True)
        
        return [{
            "erp": r.get('ma_vattu') or '---',
            "matchHeThong": r.get('ten_vattu') or 'Không tên',
            "ts": r.get('thong_so') or '',
            "hang": r.get('hang_sx') or '',
            "dvt": r.get('dvt') or 'N/A',
            "chung_loai": r.get('chung_loai') or 'Vật tư khác',
            "score": round(float(r.get('final_score', 0) * 100), 1),
            "explain": r.get('explain') # Thêm cái này để Frontend hiện "Tại sao"
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
    
    def generate_results():
        try:
            input_data = [item.dict() for item in items]
            total = len(input_data)
            
            # --- PHÒNG THỦ TẠI ĐÂY ---
            if total == 0:
                yield f"data: {json.dumps({'status': 'info', 'message': 'Danh sách trống'}, ensure_ascii=False)}\n\n"
                return

            all_results = []
            batch_size = 20
            percent = 0  # <--- KHỞI TẠO BIẾN Ở ĐÂY ĐỂ TRÁNH LỖI
            
            for i in range(0, total, batch_size):
                chunk = input_data[i : i + batch_size]
                chunk_results = bulk_matcher.process_data(chunk)
                all_results.extend(chunk_results)
                
                current_count = min(i + batch_size, total)
                percent = round((current_count / total) * 100, 2)
                
                yield f"data: {json.dumps({'status': 'progress', 'percent': percent, 'current': current_count, 'total': total}, ensure_ascii=False)}\n\n"
            
            # Gửi kết quả cuối cùng
            yield f"data: {json.dumps({'status': 'success', 'data': all_results}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            # Nếu lỗi xảy ra, print ra console để mình còn biết đường sửa tiếp
            import traceback
            print(f"🔥 LỖI TẠI MAIN: {str(e)}")
            print(traceback.format_exc()) # Dòng này sẽ hiện chi tiết lỗi nằm ở dòng nào luôn
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate_results(), media_type="text/event-stream")
    
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