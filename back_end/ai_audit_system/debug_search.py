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
    for i, hit in enumerate(hits):
        print(f"\n--- KẾT QUẢ THỨ {i+1} ---")
        print(f"📍 Kiểu dữ liệu của 'hit': {type(hit)}")
        print(f"📍 Nội dung thô của 'hit': {hit}")
        
        # Thử nghiệm cách truy cập
        try:
            print(f"✅ Thử truy cập hit.metadata: {hit.metadata if hasattr(hit, 'metadata') else 'KHÔNG CÓ ATTRIBUTE METADATA'}")
        except Exception as e:
            print(f"❌ Lỗi khi gọi .metadata: {e}")
            
        try:
            print(f"✅ Thử truy cập hit['metadata']: {hit['metadata'] if isinstance(hit, dict) and 'metadata' in hit else 'KHÔNG PHẢI DICT HOẶC KHÔNG CÓ KEY METADATA'}")
        except Exception as e:
            print(f"❌ Lỗi khi gọi ['metadata']: {e}")

if __name__ == "__main__":
    test_debug()