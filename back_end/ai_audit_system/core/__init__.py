# ai_audit_system/
# │
# ├── config/                 # Nơi chứa toàn bộ "tri thức" của hệ thống
# │   ├── materials.yaml      # Chuẩn hóa vật liệu
# │   ├── synonyms.yaml       # Từ điển đồng nghĩa Hybrid
# │   ├── units.yaml          # Chuẩn hóa đơn vị tính
# │   ├── domains.yaml        # Phân loại lĩnh vực (Valve, Pump, Sootblower...)
# │   └── weights.yaml        # Các tham số cấu hình điểm số (Scoring)
# │
# ├── core/                   # Logic cốt lõi (Không chứa dữ liệu cứng)
# │   ├── __init__.py
# │   ├── normalize.py        # Module em vừa viết
# │   ├── embedder.py         # Chạy BGE-M3 (FastEmbed/ONNX)
# │   └── vector_store.py     # Quản lý FAISS (Index/Search)
# │
# ├── data/                   # Dữ liệu thực tế
# │   ├── raw/                # File Excel gốc (ERP Master, Input)
# │   └── processed/          # Index của FAISS sau khi train xong
# │
# ├── utils/                  # Tiện ích bổ trợ
# │   ├── excel_handler.py    # Đọc/Ghi file Excel chuyên sâu
# │   └── logger.py           # Ghi log để theo dõi quá trình chạy
# │---test/
#      ├──các file test riêng biệt (test_normalize.py, test_embedder.py, test_vector_recall.py...)
# ├── pipeline.py             # File điều hướng chính (Combine everything)
# ├── main.py                 # Điểm chạy chương trình (CLI hoặc GUI sau này)
# └── requirements.txt        # Danh sách thư viện (pandas, pyyaml, fastembed, faiss-cpu...)