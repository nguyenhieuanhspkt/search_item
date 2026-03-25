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
# │   ├── reranker.py         # Chạy BGE-M3 (FastEmbed/ONNX)

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
# https://colab.research.google.com/drive/1q2-dPyWgZIEr6r_UsIk1cXp30OtZTWJf#scrollTo=V3i8KtKeGlt-

# # FAISS
# FAISS (viết tắt của Facebook AI Similarity Search) là một thư viện mã nguồn mở được phát triển bởi nhóm
# nghiên cứu AI của Meta (Facebook). Nó được thiết kế đặc biệt để giải quyết bài toán:
# Tìm kiếm các mục tương đương nhau trong một tập dữ liệu khổng lồ.
# Để Hiếu dễ hình dung trong dự án Thẩm định vật tư của mình, 
# hãy tưởng tượng FAISS giống như một "siêu thủ thư"
# có khả năng tìm ra cuốn sách có nội dung tương tự nhất trong hàng triệu cuốn sách chỉ trong vài mili giây.
# Khi có FAISS: FAISS đóng vai trò là một Index (Chỉ mục) đã được sắp xếp sẵn.
# AI chỉ việc chuyển câu hỏi thành vector, 
# còn FAISS sẽ dùng các thuật toán toán học (như phân cụm) để tìm ra kết quả trong mili giây mà không cần quét toàn bộ dữ liệu.