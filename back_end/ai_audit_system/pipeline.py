import os
import sys
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# ============================================================
# 1. ĐỊNH VỊ HỆ THỐNG (FIX LỖI IMPORT)
# ============================================================
# Tự động xác định thư mục chứa file pipeline.py này
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    # Đưa đường dẫn này lên đầu danh sách tìm kiếm của Python
    sys.path.insert(0, str(current_dir))

# Bây giờ các lệnh import core sẽ luôn tìm thấy file
try:
    from core.normalize import Normalizer
    from core.embedder import DataEmbedder
    from core.vector_store import VectorStore
    from core.reranker import Reranker
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print(f"📍 Đang tìm kiếm tại: {current_dir}")
    print("👉 Hãy đảm bảo trong thư mục 'core' có file '__init__.py'")
    sys.exit(1)

class MaterialAuditPipeline:

    def __init__(self, config_path="config"):
        # Chuyển config_path thành đường dẫn tuyệt đối để an toàn
        self.config_root = current_dir / config_path
        self.normalizer = Normalizer(str(self.config_root))
        self.embedder = DataEmbedder()
        self.vector_store = VectorStore(metric="cosine")
        self.reranker = Reranker(str(self.config_root))

    # -------------------------------------------------------------
    # STEP 1: BUILD VECTOR INDEX (Dành cho ERP Master)
    # -------------------------------------------------------------
    def build_index(self, erp_file, index_path, metadata_path):
        print(f"📌 Đang đọc dữ liệu ERP từ: {erp_file}")
        df = pd.read_excel(erp_file, engine="openpyxl")

        def _get_combined_text(row):
            # Khớp chính xác với tên cột trong ảnh bạn gửi (có dấu ngoặc)
            name = str(row.get("Tên vật tư (NXT)", row.get("Tên vật tư (N", ""))).strip()
            spec = str(row.get("Thông số kỹ thuật", "")).strip()
            s_string = str(row.get("search_string", "")).strip()
            
            # Gộp và loại bỏ nội dung trùng lặp
            parts = [name, spec, s_string]
            unique_parts = []
            for p in parts:
                if p and p.lower() not in [u.lower() for u in unique_parts]:
                    unique_parts.append(p)
            return " ".join(unique_parts)

        print("📌 Đang chuẩn hóa (Normalize) kho dữ liệu...")
        df["full_text"] = df.apply(_get_combined_text, axis=1).apply(self.normalizer.normalize)

        # Lưu Metadata (giữ nguyên tất cả các cột gốc để hiển thị kết quả)
        metadata = df.to_dict("records")

        print("📌 Đang tạo Vector Embedding (BGE-M3)...")
        vectors = self.embedder.embed_documents(df["full_text"].tolist())
        
        print("📌 Đang xây dựng chỉ mục FAISS...")
        self.vector_store.build_index(vectors, metadata)
        self.vector_store.save(index_path, metadata_path)
        print(f"✅ Build Index hoàn tất tại: {index_path}")

    # -------------------------------------------------------------
    # STEP 2: LOAD INDEX (Cho phase Search/Test)
    # -------------------------------------------------------------
    def load_index(self, index_path, metadata_path):
        """Nạp dữ liệu từ data/processed/"""
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Không tìm thấy Index: {index_path}")
        self.vector_store.load(index_path, metadata_path)
        print("🔧 FAISS Index & Metadata đã sẵn sàng.")

    # -------------------------------------------------------------
    # STEP 3: SEARCH (Hàm tìm kiếm thô phục vụ các file TEST)
    # -------------------------------------------------------------
    def search(self, query_text, top_k=5):
        """Hàm tìm kiếm đơn lẻ để kiểm tra độ nhạy AI"""
        q_norm = self.normalizer.normalize(query_text)
        vec = self.embedder.embed_query(q_norm)
        return self.vector_store.search(vec, top_k=top_k)

    # -------------------------------------------------------------
    # STEP 4: PROCESS (Quy trình thẩm định đầy đủ 102 món)
    # -------------------------------------------------------------
    def process(self, df_input):
        outputs = []
        print(f"🚀 Đang thẩm định {len(df_input)} vật tư...")

        for _, row in tqdm(df_input.iterrows(), total=len(df_input)):
            # Lấy Tên và TS từ file 102 món
            name_in = str(row.get("Tên", "N/A"))
            spec_in = str(row.get("TS", "N/A"))
            raw_query = f"{name_in} {spec_in}"

            try:
                # 1. Normalize & Search Top 50 (Recall)
                q_norm = self.normalizer.normalize(raw_query)
                vec = self.embedder.embed_query(q_norm)
                candidates = self.vector_store.search(vec, top_k=50)

                if not candidates:
                    raise ValueError("Không tìm thấy kết quả phù hợp")

                # 2. Rerank (Chấm điểm chi tiết)
                best, _ = self.reranker.rerank(q_norm, candidates)

                meta = best["metadata"]
                # Lấy tên vật tư khớp nhất từ ERP
                erp_name = meta.get("Tên vật tư (NXT)", meta.get("Tên vật tư (N", meta.get("Tên vật tư", "")))
                
                outputs.append({
                    "STT": row.get("STT", ""),
                    "Mã gốc": row.get("Mã ERP", ""),
                    "Tên gốc": name_in,
                    "TS gốc": spec_in,
                    "Mã ERP gợi ý": meta.get("Mã vật tư", ""),
                    "Tên ERP gợi ý": erp_name,
                    "Thông số ERP gợi ý": meta.get("Thông số kỹ thuật", ""),
                    "Final Score": round(best.get("final_score", 0), 4),
                    "Explain": "; ".join(best.get("reasons", ["Khớp Vector"]))
                })

            except Exception as e:
                outputs.append({
                    "STT": row.get("STT", ""),
                    "Mã gốc": row.get("Mã ERP", ""),
                    "Tên gốc": name_in,
                    "TS gốc": spec_in,
                    "Explain": f"Lỗi: {str(e)}"
                })
        
        return pd.DataFrame(outputs)