from routers import transfer
# main.py
import os
import sys
import io
import gc
import json
import shutil
import asyncio
from typing import List, Optional

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
is_model_loaded = False
# =========================================================
# 0) Thiết lập môi trường & sys.path
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Giảm đỉnh RAM do thread BLAS/OMP (đặt trước khi nạp mô hình)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# =========================================================
# 1) Import Engines (Core2 & Legacy)
# =========================================================

# Core2 (SQLite-based, nhẹ)
try:
    from core2.engine import SearchEngine as Core2Engine
    from core2.schemas import Candidate
except ImportError as e:
    print(f"⚠️ Cảnh báo: Không tìm thấy Core2: {e}")
    Core2Engine = None
    Candidate = None

# Legacy (AI BGE-M3, nặng RAM)
try:
    # Đường dẫn có thể khác tuỳ repo của bạn (vd: search_item/back_end/core/engine.py)
    # Ở đây giữ nguyên import để tương thích với code cũ của bạn.
    from core.engine import HybridSearchEngine as LegacyEngine
    from core.bulk_processor import BulkMatcher
except ImportError as e:
    print(f"⚠️ Cảnh báo: Không tìm thấy Legacy Core: {e}")
    LegacyEngine = None
    BulkMatcher = None

# =========================================================
# 2) Cấu hình app & biến toàn cục
# =========================================================

app = FastAPI(title="Hệ thống Thẩm định Vật tư Unified v2.6")

INDEX_DIR = os.path.join(BASE_DIR, "vattu_index")
MODEL_PATH = os.path.join(BASE_DIR, "AI_models", "BGE")
ADMIN_PASSWORD = "admin123"

# Global instances (lazy-load)
core2_instance = None
legacy_instance = None
bulk_matcher = None
is_ready = False

# Khoá tránh race khi nhiều request đầu tiên đến cùng lúc
_init_lock = asyncio.Lock()

# CORS mở (tuỳ chỉnh theo môi trường của bạn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Port bạn đang chạy dev
        "http://10.156.43.54:8000",   # IP thật của máy bạn
        "http://10.156.43.54:3000",   
        "*",                          # Cho phép tất cả (tạm thời để test cho nhanh)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(transfer.router)

# =========================================================
# 3) Schema inputs
# =========================================================

class MaterialInput(BaseModel):
    stt: str = ""
    ten: str = ""
    tskt: str = ""
    dvt: str = ""


# =========================================================
# 4) Startup & Lazy-load Engines
# =========================================================

@app.on_event("startup")
async def startup_event():
    """
    Không nạp Legacy/Core2 ngay để tránh chiếm RAM lớn ở thời điểm khởi động.
    Sẽ lazy-load theo `mode` khi có request đầu tiên.
    """
    global is_ready
    is_ready = True
    print("--- ✅ Service Ready (lazy-load engines on demand) ---")


async def ensure_engines(mode: str = "combined"):
    """
    Đảm bảo chỉ nạp engine cần thiết theo `mode`, có khóa tránh nạp lặp.
    """
    global core2_instance, legacy_instance, bulk_matcher

    async with _init_lock:
        # Core2
        if mode in ("core2", "combined") and (Core2Engine is not None) and (core2_instance is None):
            db_path = os.path.join(BASE_DIR, "core2", "entities.db")
            core2_instance = Core2Engine(db_path=db_path)
            print("--- ✅ Core2 Engine: Sẵn sàng ---")

        # Legacy
        if mode in ("legacy", "combined") and (LegacyEngine is not None) and (legacy_instance is None):
            legacy_instance = LegacyEngine(model_path=MODEL_PATH, index_dir=INDEX_DIR)
            if BulkMatcher is not None:
                try:
                    global bulk_matcher
                    bulk_matcher = BulkMatcher(engine=legacy_instance)
                except Exception as e:
                    print(f"⚠️ Không thể khởi tạo BulkMatcher: {e}")
            print("--- ✅ Legacy AI Engine: Sẵn sàng ---")
        is_model_loaded = True


# =========================================================
# 5) Hỗn hợp kết quả (merge)
# =========================================================

def merge_results(c2_hits, leg_hits):
    """
    Gộp kết quả từ 2 nguồn, ưu tiên mã hiệu của Core2.
    """
    merged = {}

    # 1) Nạp Core2 trước (ưu tiên mã/ERP & score của Core2)
    for r in c2_hits:
        # kỳ vọng r có: erp, matchHeThong, hang, score, explain
        merged[r['erp']] = {
            **r,
            "engine": "Core2 (Mã hiệu)",
            "score_raw": r['score'],  # lưu raw nếu cần
        }

    # 2) Nạp Legacy, xử lý trùng
    for r in leg_hits:
        erp = r.get('ma_vattu') or r.get('erp') or 'N/A'
        score = round(float(r.get('final_score', 0) * 100), 1)

        if erp in merged:
            # Hit trùng, chọn điểm cao hơn & gắn engine hỗn hợp
            merged[erp]['engine'] = "Hybrid (Mã + AI)"
            merged[erp]['score'] = max(merged[erp].get('score', 0), score)
        else:
            merged[erp] = {
                "erp": erp,
                "matchHeThong": r.get('ten_vattu') or r.get('matchHeThong'),
                "hang": r.get('hang_sx') or r.get('hang'),
                "ts": r.get('thong_so') or r.get('ts') or '',
                "dvt": r.get('dvt') or 'N/A',
                "score": score,
                "explain": r.get('explain') or "AI Semantic Match",
                "engine": "Legacy AI"
            }

    # Trả về list đã sắp theo score giảm dần
    return sorted(merged.values(), key=lambda x: x.get('score', 0), reverse=True)


# =========================================================
# 6) Endpoints
# =========================================================

@app.get("/system-status")
async def get_status():
    if not is_ready:
        return {"status": "loading", "message": "Đang nạp hệ thống..."}
    return {
        "status": "ready",
        "mode_available": ["core2", "legacy", "combined"],
        "engines_loaded": {
            "core2": core2_instance is not None,
            "legacy": legacy_instance is not None
        }
    }


@app.post("/search")
async def search_api(query: str = Form(...), mode: str = Form("combined")):
    """
    Tìm kiếm theo mode:
      - core2: chỉ Core2
      - legacy: chỉ Legacy AI
      - combined: gộp 2 nguồn và ưu tiên mã hiệu của Core2
    """
    if not is_ready:
        return {"error": "Hệ thống đang khởi động."}

    q = (query or "").strip()
    if not q:
        return []

    # Lazy-load tuỳ theo mode
    await ensure_engines(mode)

    res_c2 = []
    res_leg = []

    # Core2
    if mode in ["core2", "combined"] and core2_instance and Candidate:
        try:
            c2_out = core2_instance.search([Candidate(raw_text=q, normalized=q)])
            # Map hit của Core2 thành dict nhẹ cho FE
            res_c2 = [{
                "erp": h.model_code,
                "matchHeThong": h.name,
                "hang": h.brand,
                "score": round(h.combined * 100, 1),
                "explain": " | ".join(h.reasons)
            } for h in c2_out.hits]
        except Exception as e:
            print(f"⚠️ Core2 search error: {e}")
            res_c2 = []

    # Legacy
    if mode in ["legacy", "combined"] and legacy_instance:
        try:
            # top_k & explain tuỳ chỉnh theo nhu cầu
            res_leg = legacy_instance.search(q, top_k=5, explain=True)
        except Exception as e:
            print(f"⚠️ Legacy search error: {e}")
            res_leg = []

    # Kết quả theo mode
    if mode == "combined":
        return merge_results(res_c2, res_leg)
    elif mode == "core2":
        return res_c2
    else:
        # legacy
        return [{
            "erp": r.get('ma_vattu'),
            "matchHeThong": r.get('ten_vattu'),
            "hang": r.get('hang_sx'),
            "score": round(float(r.get('final_score', 0) * 100), 1),
            "explain": r.get('explain'),
            "engine": "Legacy AI"
        } for r in res_leg]


@app.post("/admin/rebuild-index")
async def rebuild_index(file: UploadFile = File(...), password: str = Form(...)):
    """
    Rebuild Legacy Index từ file Excel upload.
    Stream tiến độ về FE qua SSE.
    """
    if password != ADMIN_PASSWORD:
        return JSONResponse(status_code=403, content={"message": "Sai mật khẩu Admin"})

    if not legacy_instance:
        return {"error": "Legacy Engine chưa được nạp, không thể rebuild index."}

    temp_path = os.path.join(BASE_DIR, "temp_data.xlsx")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        try:
            await file.close()
        except Exception:
            pass

    def progress_stream():
        try:
            for step in legacy_instance.build_and_save_index(temp_path, overwrite=True):
                # Mỗi step là dict nhỏ: {"status": "...", "message"/"percent"/...}
                yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            # Sau build xong: reload retriever/index để bỏ ref cũ
            if hasattr(legacy_instance, "reload_index"):
                legacy_instance.reload_index()
        except Exception as e:
            yield f"data: {json.dumps({'status':'error','message':str(e)}, ensure_ascii=False)}\n\n"
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    return StreamingResponse(progress_stream(), media_type="text/event-stream")


@app.post("/extract-word")
async def extract_word(file: UploadFile = File(...)):
    """
    Trích dữ liệu bảng từ file .docx (Word). Đọc từng ô, bỏ header (row đầu).
    """
    try:
        contents = await file.read()
        doc = Document(io.BytesIO(contents))
        data = []
        for table in doc.tables:
            # Bỏ hàng tiêu đề (giả định row[0] là header)
            for row in table.rows[1:]:
                cells = row.cells
                if len(cells) >= 2:
                    data.append({
                        "stt": cells[0].text.strip(),
                        "ten": cells[1].text.strip(),
                        "ts": cells[2].text.strip() if len(cells) > 2 else "",
                        "dvt_word": cells[3].text.strip() if len(cells) > 3 else ""
                    })
        return data
    except Exception as e:
        return {"error": f"Lỗi Word: {str(e)}"}


# =========================================================
# 7) Static files (React build) – optional
# =========================================================

# Giả định frontend build tại ../front_end/dist
dist_path = os.path.join(os.path.dirname(BASE_DIR), "front_end", "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    @app.get("/")
    @app.get("/{full_path:path}")
    async def serve_react(full_path: Optional[str] = None):
        return FileResponse(os.path.join(dist_path, "index.html"))


# =========================================================
# 8) Shutdown – Thu hồi tài nguyên RAM/threads
# =========================================================

@app.on_event("shutdown")
async def shutdown_event():
    global core2_instance, legacy_instance, bulk_matcher, is_ready
    try:
        if hasattr(core2_instance, "close"):
            try:
                core2_instance.close()
            except Exception as e:
                print(f"⚠️ Lỗi đóng Core2: {e}")

        if hasattr(legacy_instance, "close"):
            try:
                legacy_instance.close()
            except Exception as e:
                print(f"⚠️ Lỗi đóng Legacy: {e}")
    finally:
        core2_instance = None
        legacy_instance = None
        bulk_matcher = None
        is_ready = False

        try:
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    print("--- 🧹 Đã shutdown & thu hồi tài nguyên ---")


# =========================================================
# 9) Dev entrypoint (không khuyến nghị --reload trong prod)
# =========================================================


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

if __name__ == "__main__":
    import uvicorn
    # Gợi ý dev: có thể dùng --reload, nhưng sẽ tốn RAM hơn khi mô hình lớn.
    uvicorn.run(app, host="0.0.0.0", port=8000)