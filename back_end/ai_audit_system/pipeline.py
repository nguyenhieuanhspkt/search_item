import os
import sys
import pandas as pd
import json
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
from ai_audit_system.core.reranker.extract import FeatureExtractor
from ai_audit_system.core.reranker.scoring import AuditScorer
from ai_audit_system.core.reranker.explain import AuditExplainer
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
    from search_item2.search_item.back_end.ai_audit_system.core.reranker.reranker import Reranker
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

class MaterialAuditPipeline:

    def __init__(self, config_path="config"):
        self.config_root = current_dir / config_path
        
        # 1. Giữ nguyên các module nền tảng
        self.normalizer = Normalizer(str(self.config_root))
        self.embedder = DataEmbedder()
        self.vector_store = VectorStore(metric="cosine")
        
        # 2. THAY THẾ: Nạp các file cấu hình YAML trước
        # (Dùng hàm load_config đã bàn ở trên)
        configs = self._load_all_configs() 
        
        # 3. THAY THẾ: Khởi tạo bộ 3 module Reranker V6.2
        self.extractor = FeatureExtractor(
            brands_list=configs['domains']['domain_rules']['brands']['keywords'],
            materials_list=configs['materials']
        )
        self.scorer = AuditScorer(weights=configs['weights'])
        self.explainer = AuditExplainer()
        
        self.threshold = configs['weights'].get('threshold', 0.85)
        self.metadata = []

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
    def _get_best_match(self, q_norm, candidates):
        """Duyệt qua các candidates từ FAISS và chấm điểm bằng Rule Engine"""
        q_features = self.extractor.get_features(q_norm)
        best_match = None
        max_score = -1

        for cand in candidates:
            # Gộp Tên và Thông số từ ERP để bóc tách features
            m_text = f"{cand.metadata.get('Tên vật tư (NXT)', '')} {cand.metadata.get('Thông số kỹ thuật', '')}"
            m_features = self.extractor.get_features(m_text)
            
            # Chấm điểm dựa trên weights.yaml
            final_score = self.scorer.calculate(q_features, m_features, cand.score)
            
            if final_score > max_score:
                max_score = final_score
                best_match = {
                    "cand": cand,
                    "q_feat": q_features,
                    "m_feat": m_features,
                    "final_score": final_score
                }
        return best_match
    
    def _audit_single_item(self, name_in, spec_in):
        raw_query = f"{name_in} {spec_in}"
        q_norm = self.normalizer.process(raw_query)
        
        # 1. Tìm kiếm ứng viên (Vòng sơ loại)
        vec = self.embedder.embed_query(q_norm)
        candidates = self.vector_store.search(vec, top_k=50)
        
        if not candidates:
            return None, "🔴 KHÔNG TÌM THẤY (ERP không có dữ liệu tương tự)"

        # 2. Chấm điểm chi tiết (Vòng chung kết)
        best = self._get_best_match(q_norm, candidates)
        
        # 3. Confidence Gate (Chặn kết quả rác)
        if best["final_score"] < self.threshold:
            return None, "🔴 KHÔNG TÌM THẤY (Không khớp mã hiệu/kỹ thuật)"

        # 4. Sinh lời phê
        explanation = self.explainer.generate(
            best["q_feat"], best["m_feat"], best["final_score"], self.threshold
        )
        
        
        # TẠO DỮ LIỆU LOG CHI TIẾT
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_query": f"{name_in} {spec_in}",
            "top_candidates_from_faiss": [
                {"text": c.text, "base_score": float(c.score)} 
                for c in candidates[:3] # Lưu lại 3 thằng đứng đầu để xem FAISS tìm đúng không
            ],
            "final_decision": {
                "matched_item": best["cand"].text if best else "NONE",
                "final_score": float(best["final_score"]) if best else 0,
                "threshold_applied": self.threshold,
                "explain": explanation
            }
        }

        # GHI VÀO FILE JSON (Chế độ append - ghi nối tiếp)
        log_path = Path("back_end/ai_audit_system/logs/audit_log.json")
        log_path.parent.mkdir(parents=True, exist_ok=True) # Tạo thư mục logs nếu chưa có
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return best, explanation
    
    def _format_output(self, row, best=None, explain=""):
        """Hàm duy nhất quản lý cấu trúc dữ liệu đầu ra"""
        # 1. Dữ liệu mặc định từ file Input của Hiếu
        base_info = {
            "STT": row.get("STT", ""),
            "Mã gốc": row.get("Mã ERP", row.get("Mã", "")),
            "Tên gốc": str(row.get("Tên", row.get("Tên vật tư", "N/A"))),
            "TS gốc": str(row.get("TS", row.get("Thông số", "N/A"))),
        }

        # 2. Nếu tìm thấy kết quả (Best Match)
        if best:
            meta = best["cand"].metadata
            result_info = {
                "Mã ERP gợi ý": meta.get("Mã vật tư", ""),
                "Tên ERP gợi ý": meta.get("Tên vật tư (NXT)", "N/A"),
                "Thông số ERP gợi ý": meta.get("Thông số kỹ thuật", ""),
                "Đơn vị tính": meta.get("Đơn vị tính", ""),
                "Final Score": round(best["final_score"], 4),
                "Explain": explain
            }
        else:
            # 3. Nếu không tìm thấy hoặc bị lỗi
            result_info = {
                "Mã ERP gợi ý": "",
                "Tên ERP gợi ý": "",
                "Thông số ERP gợi ý": "",
                "Đơn vị tính": "",
                "Final Score": 0,
                "Explain": explain
            }

        # Hợp nhất (Merge) hai túi dữ liệu lại làm một
        return {**base_info, **result_info}
    
    def process(self, df_input):
        outputs = []
        print(f"🚀 Đang khởi động thẩm định V6.2...")

        for _, row in tqdm(df_input.iterrows(), total=len(df_input)):
            try:
                # 1. Gọi logic thẩm định (Hàm này mình đã tách ở bước trước)
                name_in = str(row.get("Tên", "N/A"))
                spec_in = str(row.get("TS", "N/A"))
                best, explain = self._audit_single_item(name_in, spec_in)

                # 2. Gọi hàm Format Output để lấy dữ liệu chuẩn
                formatted_data = self._format_output(row, best, explain)
                outputs.append(formatted_data)

            except Exception as e:
                # 3. Ghi nhận lỗi theo đúng format luôn
                error_data = self._format_output(row, explain=f"⚠️ Lỗi: {str(e)}")
                outputs.append(error_data)
        
        return pd.DataFrame(outputs)