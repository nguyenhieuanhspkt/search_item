import sqlite3
import os
import json
from pathlib import Path

def init_db():
    # 1. Xác định đường dẫn tuyệt đối đến thư mục core2
    # __file__ là file init_db.py này, .parent lấy thư mục chứa nó
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "entities.db"
    
    print(f"--- Khởi tạo Database tại: {db_path} ---")

    # 2. Kết nối (Tự tạo file nếu chưa có)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Tối ưu hiệu năng SQLite
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")

        # 3. Tạo bảng Products
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_code TEXT NOT NULL,
                brand TEXT NOT NULL,
                name TEXT NOT NULL,
                spec_json TEXT NOT NULL,
                embedding BLOB,
                UNIQUE(model_code, brand)
            )
        ''')

        # 4. Tạo bảng Synonyms (Từ điển)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                canon TEXT NOT NULL
            )
        ''')

        # 5. Tạo bảng Model Alias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_alias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alias TEXT NOT NULL UNIQUE,
                model_code TEXT NOT NULL
            )
        ''')

        # 6. Tạo Index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_model ON products(model_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')

        conn.commit()
        print("✅ Khởi tạo cấu trúc bảng thành công!")

        # --- Nạp thử dữ liệu mẫu để Hiếu test luôn ---
        sample_products = [
            ('6205-2RS', 'SKF', 'Vòng bi SKF 6205-2RS', json.dumps({"type": "Bearing"})),
            ('DZ-10GW-1B', 'OMRON', 'Công tắc hành trình Omron', json.dumps({"amp": "10A"}))
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO products (model_code, brand, name, spec_json) VALUES (?,?,?,?)", 
            sample_products
        )
        
        conn.commit()
        print("✅ Đã nạp dữ liệu mẫu để sẵn sàng tìm kiếm.")

    except sqlite3.Error as e:
        print(f"❌ Lỗi SQLite: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()