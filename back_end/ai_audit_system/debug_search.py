import os
import sys
from pathlib import Path

# Thêm đường dẫn để gọi được pipeline và core
AI_SYSTEM_DIR = Path(__file__).resolve().parent
if str(AI_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SYSTEM_DIR))

try:
    from pipeline import MaterialAuditPipeline
except ImportError as e:
    print(f"❌ Không import được Pipeline: {e}")
    sys.exit(1)

def test_debug():
    print("🔍 ĐANG KIỂM TRA DỮ LIỆU ĐẦU RA CỦA HÀM SEARCH...")
    print("="*60)
    
    pipe = MaterialAuditPipeline(config_path="config")
    
    # 1. Giả định nạp FAISS (Nếu có file)
    INDEX_FILE = AI_SYSTEM_DIR / "data" / "processed" / "faiss.index"
    META_FILE  = AI_SYSTEM_DIR / "data" / "processed" / "faiss_meta.pkl"
    
    if INDEX_FILE.exists():
        pipe.load_index(str(INDEX_FILE), str(META_FILE))
    
    # 2. Test thử 1 câu truy vấn
    query = "vòng bi SKF 6205"
    q_norm = pipe.normalizer.normalize(query)
    vec = pipe.embedder.embed_query(q_norm)
    
    # GỌI HÀM SEARCH CỦA VECTOR STORE
    print(f"📡 Đang search thử cụm từ: '{query}'")
    hits = pipe.vector_store.search(vec, top_k=2)
    
    if not hits:
        print("❌ Không tìm thấy kết quả nào!")
        return

    # --- ĐOẠN DEBUG QUAN TRỌNG NHẤT ---
# --- ĐOẠN DEBUG QUAN TRỌNG NHẤT (V6.2 - AUTO DETECT) ---
    for i, hit in enumerate(hits):
        print(f"\n--- KẾT QUẢ THỨ {i+1} (Score: {hit.get('score', 0):.4f}) ---")
        
        meta = hit.get('metadata', {})
        
        # 1. IN TẤT CẢ KEYS ĐỂ HIẾU KIỂM TRA Tên Cột Thực Tế
        all_keys = list(meta.keys())
        print(f"🔑 CÁC CỘT ĐANG CÓ TRONG FAISS: {all_keys}")

        # 2. DÒ TÌM CỘT GIÁ (Ưu tiên 'Đơn Giá Nhập' của Hiếu)
        # Thêm các biến thể nếu Excel viết hoa/thường khác nhau
        price_keys = ['Đơn Giá Nhập', 'Đơn giá', 'Giá', 'Price', 'unit_price']
        found_price = "❌ CHƯA CÓ TRONG FAISS"
        
        for pk in price_keys:
            if pk in meta:
                found_price = meta[pk]
                print(f"✅ Đã tìm thấy giá ở cột: '{pk}'")
                break
        
        # 3. DÒ TÌM CỘT DIỄN GIẢI / THÔNG SỐ
        desc_keys = ['Thông số kỹ thuật', 'Diễn giải', 'Mô tả', 'Description']
        found_desc = "❌ CHƯA CÓ TRONG FAISS"
        
        for dk in desc_keys:
            if dk in meta:
                found_desc = meta[dk]
                print(f"✅ Đã tìm thấy diễn giải ở cột: '{dk}'")
                break

        # 4. IN KẾT QUẢ CUỐI CÙNG
        print(f"📍 Mã vật tư: {meta.get('Mã vật tư', 'KHÔNG THẤY')}")
        print(f"📍 Tên vật tư: {meta.get('Tên vật tư (NXT)', 'KHÔNG THẤY')}")
        print(f"💰 Giá tìm thấy: {found_price}")
        print(f"📝 Diễn giải: {found_desc}")

if __name__ == "__main__":
    test_debug()