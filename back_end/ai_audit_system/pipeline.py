import os
import sys
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# --- IMPORT BỘ 3 QUYỀN LỰC & CORE ---
try:
    from core.normalize import Normalizer
    from core.embedder import DataEmbedder as BGEEmbedder 
    from core.vector_store import VectorStore
    
    # Reranker 3 lớp
    from core.reranker.extract import FeatureExtractor
    from core.reranker.scoring import AuditScorer
    from core.reranker.explain import AuditExplainer
except ImportError as e:
    print(f"⚠️ Lỗi Import Core: {e}. Hiếu kiểm tra lại folder core/ nhé!")

class MaterialAuditPipeline: 
    def __init__(self, config_path="config"):
        # 1. Định vị folder config
        self.current_dir = Path(__file__).resolve().parent
        self.config_root = self.current_dir / config_path
        
        # 2. Nạp cấu hình YAML (Weights, Domains, Materials)
        self.configs = self._load_all_configs()
        
        # 3. Khởi tạo các module core
        self.normalizer = Normalizer(config_path=str(self.config_root))
        self.embedder = BGEEmbedder() 
        self.vector_store = VectorStore(metric="cosine")
        
        # 4. Khởi tạo bộ 3 Reranker
        self.extractor = FeatureExtractor(
            brands_list=self.configs['domains'].get('domain_rules', {}).get('brands', {}).get('keywords', []),
            materials_list=self.configs.get('materials', [])
        )
        self.scorer = AuditScorer(weights=self.configs['weights'])
        self.explainer = AuditExplainer()
        
        # 5. Ngưỡng an toàn & Cache
        self.threshold = self.configs['weights'].get('threshold', 0.85)
        self.audit_cache = {}

    def _load_all_configs(self):
        """Nạp cấu hình và phẳng hóa materials"""
        configs = {'domains': {}, 'weights': {'threshold': 0.85}, 'materials': []}
        try:
            for name in ['weights', 'domains']:
                p = self.config_root / f"{name}.yaml"
                if p.exists():
                    with open(p, 'r', encoding='utf-8') as f:
                        configs[name] = yaml.safe_load(f) or configs[name]
            
            m_path = self.config_root / "materials.yaml"
            if m_path.exists():
                with open(m_path, 'r', encoding='utf-8') as f:
                    m_data = yaml.safe_load(f).get('materials', [])
                    flat_m = []
                    for item in m_data:
                        if isinstance(item, dict):
                            flat_m.append(str(item.get('canonical', '')))
                            flat_m.extend([str(a) for a in item.get('aliases', [])])
                        else: flat_m.append(str(item))
                    configs['materials'] = list(set(filter(None, flat_m)))
        except Exception as e:
            print(f"⚠️ Lỗi cấu hình YAML: {e}")
        return configs

    # ============================================================
    # QUẢN LÝ BỘ NHỚ AI (FAISS) - Gọi từ main.py
    # ============================================================
    def load_index(self, index_path, metadata_path):
        """Nạp Index và Metadata cho FAISS"""
        self.vector_store.load(index_path, metadata_path)
        print(f"🔧 Đã nạp thành công bộ nhớ AI ({len(self.vector_store.metadata)} dòng).")

    def build_index(self, erp_file, index_path, metadata_path):
        """Xây dựng mới Index FAISS từ file Excel Master"""
        print(f"📌 Đang xây dựng bộ nhớ AI từ: {Path(erp_file).name}")
        df = pd.read_excel(erp_file)
        
        # Tự động tìm cột (linh hoạt cho Hiếu)
        name_col = next((c for c in df.columns if "Tên" in c), df.columns[1])
        spec_col = next((c for c in df.columns if "Thông số" in c or "TS" in c), None)
        
        tqdm.pandas(desc="Chuẩn hóa Master Data")
        df['full_text_norm'] = df.progress_apply(
            lambda r: self.normalizer.normalize(f"{r[name_col]} {r[spec_col] if spec_col else ''}"), 
            axis=1
        )

        print("📌 Đang tạo Vector Embedding (BGE-M3)...")
        vectors = self.embedder.embed_documents(df['full_text_norm'].tolist())
        
        self.vector_store.build_index(vectors, df.to_dict("records"))
        self.vector_store.save(index_path, metadata_path)
        print(f"✅ Build Index hoàn tất.")

    # ============================================================
    # LOGIC THẨM ĐỊNH (PHỐI HỢP EXTRACT - SCORE - EXPLAIN)
    # ============================================================
    def _run_audit_single(self, name_query, spec_query=""):
        """
        Luồng thẩm định chi tiết: Extract -> Vector Search -> Scoring -> Explain
        Hỗ trợ cả dữ liệu dạng Dict (Meili) và Object (FAISS)
        """
        query_raw = f"{name_query} {spec_query}".strip()
        
        # 1. Kiểm tra Cache để tăng tốc nếu trùng câu hỏi
        if query_raw in self.audit_cache: 
            return self.audit_cache[query_raw]
        
        # 2. Chuẩn hóa và bóc tách đặc tính câu hỏi (EXTRACT)
        q_norm = self.normalizer.normalize(query_raw)
        q_feat = self.extractor.get_features(q_norm)
        
        # 3. Tìm kiếm ứng viên (FAISS / Vector Store)
        vec = self.embedder.embed_query(q_norm)
        hits = self.vector_store.search(vec, top_k=50)
        
        if not hits:
            return None

        scored_results = []
        for hit in hits:
            meta = hit.get('metadata', {})
            score_raw = hit.get('score', 0) 
            
            # --- LẤY THÊM DỮ LIỆU GIÁ VÀ DIỄN GIẢI ---
            m_name = meta.get('Tên vật tư (NXT)', '')
            m_spec = meta.get('Thông số kỹ thuật', '')
            m_code = meta.get('Mã vật tư', 'N/A')
            m_unit = meta.get('Đơn vị tính', 'N/A')
            
            # Cột giá và diễn giải (Hiếu kiểm tra đúng tên cột trong file Excel 20015 dòng nhé)
            m_price = meta.get('Đơn giá', meta.get('Giá', 0)) 
            m_desc  = meta.get('Diễn giải', meta.get('Mô tả', ''))
            
            m_text_full = f"{m_name} {m_spec}".strip()
            
            # --- CHẠY RERANKER ---
            m_feat = self.extractor.get_features(m_text_full)
            final_score = self.scorer.calculate(q_feat, m_feat, score_raw)
            explanation = self.explainer.generate(q_feat, m_feat, final_score, self.threshold)
            
            scored_results.append({
                "score": final_score,
                "material_code": m_code,
                "full_name": m_text_full,
                "unit": m_unit,
                "price": m_price,      # Thêm vào đây
                "description": m_desc,  # Thêm vào đây
                "explain": explanation
            })
        
        # 7. Sắp xếp theo điểm số từ cao xuống thấp
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Lưu vào cache và trả về
        self.audit_cache[query_raw] = scored_results
        return scored_results

    def _format_output(self, row, best=None, error_msg=None):
        """Cập nhật cấu trúc bảng Excel đầu ra"""
        base = {
            "STT": row.get("STT", ""),
            "Tên gốc": row.get("Tên", ""),
            "TS gốc": row.get("TS", "")
        }
        if error_msg: return {**base, "Kết luận": f"⚠️ Lỗi: {error_msg}"}
        
        if best and best['score'] >= self.threshold:
            return {
                **base,
                "Mã ERP gợi ý": best["material_code"],
                "Tên gợi ý": best["full_name"],
                "Đơn vị": best["unit"],
                "Giá ERP": best["price"],        # Cột mới
                "Diễn giải ERP": best["description"], # Cột mới
                "Độ tin cậy": round(best["score"], 4),
                "Lời phê AI": best["explain"],
                "Kết luận": "✅ ĐẠT"
            }

    def process(self, df_input):
        """Hàm chính quét lô 102 món và trả về DataFrame"""
        final_rows = []
        
        # Nhận diện cột linh hoạt
        name_col = next((c for c in df_input.columns if "Tên" in c), "Tên")
        spec_col = next((c for c in df_input.columns if "TS" in c or "Thông số" in c), "TS")

        for _, row in tqdm(df_input.iterrows(), total=len(df_input), desc="AI Auditing"):
            try:
                res = self._run_audit_single(str(row.get(name_col, "")), str(row.get(spec_col, "")))
                best = res[0] if res else None
                final_rows.append(self._format_output(row, best=best))
            except Exception as e:
                final_rows.append(self._format_output(row, error_msg=str(e)))

        return pd.DataFrame(final_rows)