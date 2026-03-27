import os
import sys
import io
import gc
import json
import shutil
import asyncio
import pandas as pd
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document

# =========================================================
# 0) Thiết lập môi trường & sys.path (QUAN TRỌNG)
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Tối ưu cho CPU máy nhà
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

app = FastAPI(title="Hệ thống Thẩm định Vật tư Unified v3.0")

# =========================================================
# 1) Import các Engines
# =========================================================
try:
    from core2.engine import SearchEngine as Core2Engine
    from core2.schemas import Candidate
except ImportError:
    Core2Engine = None

try:
    from core.engine import HybridSearchEngine as LegacyEngine
    from core.bulk_processor import BulkMatcher
except ImportError:
    LegacyEngine = None
    BulkMatcher = None

# Router phụ
try:
    from routers import transfer
    app.include_router(transfer.router)
except ImportError:
    pass

# =========================================================
# 2) Cấu hình đường dẫn & Biến toàn cục
# =========================================================
INDEX_DIR = BASE_DIR / "vattu_index"
MODEL_PATH = BASE_DIR / "AI_models" / "BGE"
ADMIN_PASSWORD = "admin123"

core2_instance = None
legacy_instance = None
bulk_matcher = None
is_ready = False
_init_lock = asyncio.Lock()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MaterialInput(BaseModel):
    stt: str = ""
    ten: str = ""
    tskt: str = ""
    dvt: str = ""

# =========================================================
# 3) Startup & Lazy-load
# =========================================================
@app.on_event("startup")
async def startup_event():
    global is_ready
    is_ready = True
    print("--- ✅ Backend Server Ready ---")

async def ensure_engines(mode: str = "combined"):
    global core2_instance, legacy_instance, bulk_matcher
    async with _init_lock:
        if mode in ("core2", "combined") and core2_instance is None and Core2Engine:
            db_path = BASE_DIR / "core2" / "entities.db"
            core2_instance = Core2Engine(db_path=str(db_path))
            print("--- ✅ Core2 Engine: Sẵn sàng ---")

        if mode in ("legacy", "combined") and legacy_instance is None and LegacyEngine:
            legacy_instance = LegacyEngine(model_path=str(MODEL_PATH), index_dir=str(INDEX_DIR))
            if BulkMatcher:
                bulk_matcher = BulkMatcher(engine=legacy_instance)
            print("--- ✅ Legacy AI Engine: Sẵn sàng ---")

# =========================================================
# 4) Endpoints chính
# =========================================================

@app.get("/system-status")
async def get_status():
    return {"status": "ready" if is_ready else "loading"}

# --- TÍNH NĂNG SEARCH ĐƠN LẺ ---
@app.post("/search")
async def search_api(query: str = Form(...), mode: str = Form("combined")):
    q = query.strip()
    if not q: return []
    await ensure_engines(mode)
    
    res_c2 = []
    if mode in ["core2", "combined"] and core2_instance:
        c2_out = core2_instance.search([Candidate(raw_text=q, normalized=q)])
        res_c2 = [{"erp": h.model_code, "matchHeThong": h.name, "hang": h.brand, "score": round(h.combined * 100, 1), "explain": " | ".join(h.reasons)} for h in c2_out.hits]

    res_leg = []
    if mode in ["legacy", "combined"] and legacy_instance:
        res_leg = legacy_instance.search(q, top_k=5, explain=True)
        # Re-format legacy hits
        res_leg = [{"erp": r.get('ma_vattu'), "matchHeThong": r.get('ten_vattu'), "hang": r.get('hang_sx'), "score": round(float(r.get('final_score', 0) * 100), 1), "explain": r.get('explain'), "engine": "Legacy AI"} for r in res_leg]

    if mode == "combined":
        # Merge đơn giản
        return sorted(res_c2 + res_leg, key=lambda x: x['score'], reverse=True)
    return res_c2 if mode == "core2" else res_leg


# Thêm hàm bổ trợ để gộp kết quả (giống logic trong search_api)
async def get_combined_result(q: str):
    """Logic gộp Core2 và Legacy y hệt như Search đơn lẻ"""
    await ensure_engines("combined")
    
    res_c2 = []
    if core2_instance:
        c2_out = core2_instance.search([Candidate(raw_text=q, normalized=q)])
        res_c2 = [{"erp": h.model_code, "matchHeThong": h.name, "hang": h.brand, 
                   "score": round(h.combined * 100, 1), "explain": " | ".join(h.reasons)} for h in c2_out.hits]

    res_leg = []
    if legacy_instance:
        # Lấy top 1 thôi cho nhanh vì là bulk
        leg_out = legacy_instance.search(q, top_k=1, explain=True)
        res_leg = [{"erp": r.get('ma_vattu'), "matchHeThong": r.get('ten_vattu'), "hang": r.get('hang_sx'), 
                   "score": round(float(r.get('final_score', 0) * 100), 1), 
                   "explain": r.get('explain'), "engine": "Legacy AI"} for r in leg_out]

    # Gộp và lấy thằng cao điểm nhất
    combined = sorted(res_c2 + res_leg, key=lambda x: x['score'], reverse=True)
    return combined[0] if combined else None





# --- TÍNH NĂNG THẨM ĐỊNH LÔ (BULK MATCH) ---
@app.post("/api/bulk-match")
async def handle_bulk_match(items: List[MaterialInput]):
    # Đảm bảo các engine đã sẵn sàng
    await ensure_engines("combined")

    def generate_results():
        try:
            total = len(items)
            # Vì dùng async/await bên trong loop nên ta không dùng bulk_matcher.process_data nữa
            # mà chạy trực tiếp loop ở đây để tận dụng logic Combined
            
            for i, item in enumerate(items):
                q = f"{item.ten} {item.tskt}".strip()
                
                # Gọi logic "kế thừa" từ search đơn lẻ
                # Lưu ý: Vì loop này chạy đồng bộ trong generator, 
                # ta dùng cách chạy async trong thread hoặc chạy tuần tự
                import asyncio
                best_match = asyncio.run(get_combined_result(q))
                
                # Format kết quả để trả về giống cấu trúc cũ của Hiếu
                result = []
                if best_match:
                    # Tạo highlight đơn giản nếu cần (hoặc dùng hàm của bulk_matcher cũ)
                    result.append({
                        "stt": item.stt or str(i+1),
                        "matchHeThong": best_match['matchHeThong'],
                        "erp": best_match['erp'],
                        "dvt": best_match.get('dvt', 'N/A'),
                        "score": best_match['score'] / 100, # Chuyển về hệ 0-1 nếu FE cần
                        "explain": best_match['explain'],
                        "engine": best_match.get('engine', 'Combined')
                    })
                
                percent = round(((i + 1) / total) * 100, 2)
                yield f"data: {json.dumps({'status': 'progress', 'percent': percent, 'data': result}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'status': 'success'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            print(f"🔥 Lỗi Bulk: {e}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate_results(), media_type="text/event-stream")

# --- TRÍCH XUẤT WORD ---
@app.post("/extract-word")
async def extract_word(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        doc = Document(io.BytesIO(contents))
        data = []
        for table in doc.tables:
            for row in table.rows[1:]: # Bỏ header
                cells = row.cells
                if len(cells) >= 2:
                    data.append({
                        "stt": cells[0].text.strip(),
                        "ten": cells[1].text.strip(),
                        "ts": cells[2].text.strip() if len(cells) > 2 else "",
                        "dvt": cells[3].text.strip() if len(cells) > 3 else ""
                    })
        return data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)