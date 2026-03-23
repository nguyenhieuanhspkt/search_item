# core2/db.py
import sqlite3
from typing import List, Dict, Any, Optional

class DB:
    def __init__(self, path: str, enable_fk=True, wal=True):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        if enable_fk:
            self.conn.execute("PRAGMA foreign_keys=ON")
        if wal:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    # ---------- DAO examples ----------
    def get_canon(self, term: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT canon FROM synonyms WHERE term = ?",
            (term.lower(),)
        ).fetchone()
        return row["canon"] if row else None

    def find_model_code_by_alias(self, alias: str) -> Optional[str]:
        if not alias: return None
        
        # Làm sạch: Bỏ dấu cách đầu cuối và đưa về chữ HOA
        clean_alias = alias.strip().upper()
        
        row = self.conn.execute(
            "SELECT model_code FROM model_alias WHERE UPPER(alias) = ?",
            (clean_alias,)
        ).fetchone()
        
        return row["model_code"] if row else None

    def fetch_products_by_model_brand(
        self, model_code: str, brand: Optional[str] = None
    ) -> List[sqlite3.Row]:
        if brand:
            q = "SELECT * FROM products WHERE model_code=? AND brand=?"
            return self.conn.execute(q, (model_code, brand)).fetchall()
        q = "SELECT * FROM products WHERE model_code=?"
        return self.conn.execute(q, (model_code,)).fetchall()

    def search_like(self, term: str, limit=20) -> List[sqlite3.Row]:
        # fallback LIKE search khi chưa gắn Whoosh
        t = f"%{term}%"
        q = """SELECT *, 
               CASE WHEN name LIKE ? THEN 1.0 ELSE 0.0 END AS kscore
               FROM products
               WHERE name LIKE ? OR model_code LIKE ? OR brand LIKE ?
               ORDER BY kscore DESC
               LIMIT ?"""
        return self.conn.execute(q, (t, t, t, t, limit)).fetchall()