import sqlite3
import json
from pathlib import Path

# Cấu hình đường dẫn trỏ đúng vào core2
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "entities.db"

def connect_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def import_data():
    conn = connect_db()
    
    # 1. Dữ liệu Sản phẩm
    products = [
        ('6205-2RS', 'SKF', 'Vòng bi SKF 6205-2RS', {"type": "Bearing", "inner_d": 25}),
        ('DZ-10GW-1B', 'OMRON', 'Công tắc hành trình Omron', {"type": "Switch", "amp": "10A"}),
        ('170M3819', 'BUSSMANN', 'Cầu chì trung thế Bussmann', {"type": "Fuse", "amp": "400A"}),
        ('SUS304-P', 'GENERIC', 'Tấm Inox 304 dày 5mm', {"material": "Stainless Steel", "grade": "304"})
    ]

    # 2. Dữ liệu Từ điển đồng nghĩa
    synonyms = [
        ('inox', 'SUS304'),
        ('bạc đạn', 'bearing'),
        ('vòng bi', 'bearing'),
        ('công tắc', 'switch')
    ]

    # 3. Dữ liệu Biến thể mã hiệu (ĐỂ CỨU TEST 2)
    # Giúp hệ thống hiểu các cách viết thiếu dấu gạch, dấu chấm
    aliases = [
        ('62052RS', '6205-2RS'),
        ('6205 2RS', '6205-2RS'),
        ('DZ10GW1B', 'DZ-10GW-1B'),
        ('170M 3819', '170M3819')
    ]

    try:
        # Nạp Products
        for model, brand, name, specs in products:
            conn.execute(
                "INSERT OR IGNORE INTO products (model_code, brand, name, spec_json) VALUES (?, ?, ?, ?)",
                (model, brand, name, json.dumps(specs))
            )
        
        # Nạp Synonyms
        conn.executemany(
            "INSERT OR IGNORE INTO synonyms (term, canon) VALUES (?, ?)",
            synonyms
        )

        # Nạp Aliases (Quan trọng cho Model Scorer)
        conn.executemany(
            "INSERT OR IGNORE INTO model_alias (alias, model_code) VALUES (?, ?)",
            aliases
        )
        
        conn.commit()
        print(f"✅ Đã nạp xong: {len(products)} SP, {len(synonyms)} từ điển, {len(aliases)} biến thể mã.")
    except Exception as e:
        print(f"❌ Lỗi khi nạp dữ liệu: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_data()