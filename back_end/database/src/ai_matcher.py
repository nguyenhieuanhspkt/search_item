import sys
import os
import asyncio
import pandas as pd
from pathlib import Path

# --- THIẾT LẬP ĐƯỜNG DẪN GỐC ---
CURRENT_FILE = Path(__file__).resolve()
# Nhảy ngược 3 cấp từ src -> database -> back_end
BACKEND_ROOT = CURRENT_FILE.parent.parent.parent 

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# --- IMPORT TRỰC TIẾP TỪ ENGINES (Bỏ qua main.py) ---
HAS_AI = False
core2_instance = None
legacy_instance = None
_init_lock = asyncio.Lock()

try:
    from core2.engine import SearchEngine as Core2Engine
    from core2.schemas import Candidate
    from core.engine import HybridSearchEngine as LegacyEngine
    HAS_AI = True
except ImportError as e:
    print(f"⚠️ Lỗi nạp Engines: {e}")

# --- 1. HÀM KHỞI ĐỘNG ENGINES ---
async def ensure_engines_internal():
    global core2_instance, legacy_instance
    async with _init_lock:
        if core2_instance is None:
            print("⏳ 1/3: Đang nạp Core2 Engine (Database)...")
            db_path = BACKEND_ROOT / "core2" / "entities.db"
            core2_instance = Core2Engine(db_path=str(db_path))
            
        if legacy_instance is None:
            print("⏳ 2/3: Đang nạp BGE-M3 Model (Rất nặng, xin đợi 1-2 phút)...")
            model_path = BACKEND_ROOT / "AI_models" / "BGE"
            index_dir = BACKEND_ROOT / "vattu_index"
            legacy_instance = LegacyEngine(model_path=str(model_path), index_dir=str(index_dir))
            print("✅ 3/3: Hệ thống AI đã sẵn sàng!")
def init_ai_engine():
    """Hàm cầu nối cho processors.py gọi"""
    if not HAS_AI: return False
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nếu đang trong luồng async khác (ít gặp ở script này)
            return True 
        loop.run_until_complete(ensure_engines_internal())
        return True
    except Exception as e:
        print(f"❌ Lỗi khởi động AI: {e}")
        return False

# --- 2. LOGIC GỘP KẾT QUẢ (COMBINED SEARCH) ---
async def get_combined_result_internal(q: str):
    """Logic gộp Core2 và Legacy y hệt như App Unified v3.0"""
    query = q.strip()
    if not query: return None

    # A. Chạy Core2 (Entity Search)
    res_c2 = []
    if core2_instance:
        c2_out = core2_instance.search([Candidate(raw_text=query, normalized=query)])
        res_c2 = [{
            "erp": h.model_code, 
            "matchHeThong": h.name, 
            "score": round(h.combined * 100, 1), 
            "explain": " | ".join(h.reasons),
            "engine": "Core2"
        } for h in c2_out.hits]

    # B. Chạy Legacy (BGE-M3 Embedding)
    res_leg = []
    if legacy_instance:
        leg_hits = legacy_instance.search(query, top_k=1, explain=True)
        res_leg = [{
            "erp": r.get('ma_vattu'), 
            "matchHeThong": r.get('ten_vattu'), 
            "score": round(float(r.get('final_score', 0) * 100), 1), 
            "explain": r.get('explain'), 
            "engine": "Legacy AI"
        } for r in leg_hits]

    # C. Gộp và lấy kết quả cao điểm nhất
    combined = sorted(res_c2 + res_leg, key=lambda x: x['score'], reverse=True)
    return combined[0] if combined else None

# --- 3. HÀM XỬ LÝ BATCH (DÙNG CHO PROCESSORS.PY) ---
def process_ai_audit_batch(df_input):
    """Xử lý quét AI cho danh sách vật tư"""
    results = []
    loop = asyncio.get_event_loop()
    
    total = len(df_input)
    print(f"🤖 Đang AI-Audit {total} dòng bằng BGE-M3 & Core2...")

    for i, (_, row) in enumerate(df_input.iterrows()):
        query = str(row['TVT']).strip()
        
        # Chạy logic gộp internal
        match = loop.run_until_complete(get_combined_result_internal(query))
        
        if match:
            results.append({
                'Ma_ERP_AI': match['erp'],
                'Ten_ERP_AI': match['matchHeThong'],
                'Score_AI': match['score'],
                'Explain_AI': match['explain'],
                'AI_Engine': match['engine']
            })
        else:
            results.append({
                'Ma_ERP_AI': None, 'Ten_ERP_AI': "KHÔNG KHỚP", 
                'Score_AI': 0, 'Explain_AI': "", 'AI_Engine': "None"
            })
            
        if (i + 1) % 50 == 0:
            print(f"   ∟ Tiến độ AI: {i+1}/{total} dòng...")

    return pd.DataFrame(results)