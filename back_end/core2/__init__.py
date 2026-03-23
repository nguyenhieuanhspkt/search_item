    # search_item/back_end/core2/
    # ├── __init__.py
    # ├── preprocessor.py  # Chuyên làm sạch, bóc tách thông số/mã hiệu
    # ├── model_scorer.py Chấm điểm đạt chỉ tiêu model hay không
    # ├── dictionary.py    # Chứa từ điển đồng nghĩa (Inox = SUS) và quy đổi đơn vị
    # ├── retriever.py     # Tìm kiếm đa luồng (Whoosh + Vector Search)
    # ├── validator.py     # Bộ quy tắc Thưởng/Phạt (Business Rules)
    # └── engine.py        # Nhạc trưởng điều phối các file trên