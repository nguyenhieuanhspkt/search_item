import os
import sys
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# ============================================================
# 1. ĐỊNH VỊ HỆ THỐNG (FIX LỖI IMPORT)
# ============================================================
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from core.normalize import Normalizer
    from core.embedder import DataEmbedder
    from core.vector_store import VectorStore
    from core.reranker import Reranker
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

class MaterialAuditPipeline:

    def __init__(self, config_path="config"):
        self.config_root = current_dir / config_path
        self.normalizer = Normalizer(str(self.config_root))
        self.embedder = DataEmbedder()
        self.vector_store = VectorStore(metric="cosine")
        self.reranker = Reranker(str(self.config_root))
        self.metadata = [] # Để lưu trữ metadata sau khi load

    # -------------------------------------------------------------
    # STEP 1: BUILD VECTOR INDEX (Dành cho ERP Master)
    # -------------------------------------------------------------
    def build_index(self, erp_file, index_path, metadata_path):
        print(f"📌 Đang đọc dữ liệu ERP từ: {erp_file}")
        df = pd.read_excel(erp_file, engine="openpyxl")

        def _get_combined_text(row):
            # Hỗ trợ nhiều biến thể tên cột để tránh lỗi N/A
            name = str(row.get("Tên vật tư (NXT)", row.get("Tên vật tư (N", ""))).strip()
            spec = str(row.get("Thông số kỹ thuật", "")).strip()
            s_string = str(row.get("search_string", "")).strip()
            
            parts = [name, spec, s_string]
            unique_parts = []
            for p in parts:
                if p and p.lower() not in [u.lower() for u in unique_parts]:
                    unique_parts.append(p)
            return " ".join(unique_parts)

        print("📌 Đang chuẩn hóa (Normalize) kho dữ liệu...")
        df["full_text"] = df.apply(_get_combined_text, axis=1).apply(self.normalizer.normalize)

        self.metadata = df.to_dict("records")

        print("📌 Đang tạo Vector Embedding (BGE-M3)...")
        vectors = self.embedder.embed_documents(df["full_text"].tolist())
        
        print("📌 Đang xây dựng chỉ mục FAISS...")
        self.vector_store.build_index(vectors, self.metadata)
        self.vector_store.save(index_path, metadata_path)
        print(f"✅ Build Index hoàn tất tại: {index_path}")

    # -------------------------------------------------------------
    # STEP 2: LOAD INDEX (Cho phase Search/Test)
    # -------------------------------------------------------------
    def load_index(self, index_path, metadata_path):
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Không tìm thấy Index: {index_path}")
        self.vector_store.load(index_path, metadata_path)
        # Cập nhật lại metadata vào instance để file Test có thể truy cập
        self.metadata = self.vector_store.metadata if hasattr(self.vector_store, 'metadata') else []
        print(f"🔧 FAISS Index & Metadata ({len(self.metadata)} dòng) đã sẵn sàng.")

    # -------------------------------------------------------------
    # STEP 3: SEARCH (Sửa lại để luôn lấy từ túi metadata)
    # -------------------------------------------------------------
    def search(self, query_text, top_k=5):
        q_norm = self.normalizer.normalize(query_text)
        vec = self.embedder.embed_query(q_norm)
        return self.vector_store.search(vec, top_k=top_k)

    # -------------------------------------------------------------
    # STEP 4: PROCESS (Quy trình thẩm định 102 món)
    # -------------------------------------------------------------
    def process(self, df_input):
        outputs = []
        print(f"🚀 Đang thẩm định {len(df_input)} vật tư...")

        for _, row in tqdm(df_input.iterrows(), total=len(df_input)):
            # Tên và Thông số từ file 102 món của Hiếu
            name_in = str(row.get("Tên", row.get("Tên vật tư", "N/A")))
            spec_in = str(row.get("TS", row.get("Thông số", "N/A")))
            raw_query = f"{name_in} {spec_in}"

            try:
                q_norm = self.normalizer.normalize(raw_query)
                vec = self.embedder.embed_query(q_norm)
                candidates = self.vector_store.search(vec, top_k=50)

                if not candidates:
                    raise ValueError("Không tìm thấy kết quả phù hợp")

                # Rerank để lấy kết quả tốt nhất
                best, _ = self.reranker.rerank(q_norm, candidates)

                # LẤY DỮ LIỆU TỪ TÚI METADATA (QUAN TRỌNG)
                meta = best.get("metadata", best) # Phòng hờ trường hợp reranker trả về meta phẳng
                
                # Tìm tên vật tư từ ERP (thử các biến thể cột)
                erp_name = meta.get("Tên vật tư (NXT)", meta.get("Tên vật tư (N", "Không rõ tên"))
                
                outputs.append({
                    "STT": row.get("STT", ""),
                    "Mã gốc": row.get("Mã ERP", row.get("Mã", "")),
                    "Tên gốc": name_in,
                    "TS gốc": spec_in,
                    "Mã ERP gợi ý": meta.get("Mã vật tư", ""),
                    "Tên ERP gợi ý": erp_name,
                    "Thông số ERP gợi ý": meta.get("Thông số kỹ thuật", ""),
                    "Đơn vị tính": meta.get("Đơn vị tính", ""),
                    "Final Score": round(best.get("final_score", 0), 4),
                    "Explain": "; ".join(best.get("reasons", ["Khớp ngữ nghĩa"]))
                })

            except Exception as e:
                outputs.append({
                    "STT": row.get("STT", ""),
                    "Tên gốc": name_in,
                    "Explain": f"Lỗi xử lý: {str(e)}"
                })
        
        return pd.DataFrame(outputs)