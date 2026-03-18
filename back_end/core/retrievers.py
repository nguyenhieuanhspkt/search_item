# search_item/back_end/core/retrievers.py
from __future__ import annotations
import os
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from whoosh.index import open_dir, create_in, exists_in
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import MultifieldParser, OrGroup

@dataclass
class WhooshFields:
    """Định nghĩa các trường dữ liệu - Khớp với cấu hình hệ thống"""
    id_field: str = "ma_vattu"
    name_field: str = "ten_vattu"
    spec_field: str = "thong_so"
    brand_field: str = "hang_sx"
    category_field: str = "chung_loai"
    unit_field: str = "dvt"
    all_text_field: str = "all_text"
    query_fields: Tuple[str, ...] = ("ten_vattu", "thong_so", "all_text")

class WhooshRetriever:
    def __init__(self, index_dir: str, fields: Optional[WhooshFields] = None):
        self.index_dir = index_dir
        self.fields = fields or WhooshFields()

    def schema(self) -> Schema:
        f = self.fields
        return Schema(**{
            f.id_field: ID(stored=True),
            f.name_field: TEXT(stored=True),
            f.spec_field: TEXT(stored=True),
            f.brand_field: TEXT(stored=True),
            f.category_field: TEXT(stored=True),
            f.unit_field: STORED,
            f.all_text_field: TEXT(stored=True),
        })

    def open(self):
        if not exists_in(self.index_dir):
            os.makedirs(self.index_dir, exist_ok=True)
            create_in(self.index_dir, self.schema())
        return open_dir(self.index_dir)

    def build_index_from_dataframe(
        self, 
        df: pd.DataFrame, 
        predict_category_fn: Optional[Callable[[str], str]] = None,
        overwrite: bool = True
    ) -> bool:
        """Xây dựng index có giới hạn tài nguyên để tránh treo máy i5"""
        try:
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)

            ix = create_in(self.index_dir, self.schema())
            # Tối ưu: limitmb=256 giúp Whoosh không ăn quá nhiều RAM khi build
            writer = ix.writer(limitmb=256) 

            f = self.fields
            for _, row in df.iterrows():
                ten = str(row.get("Tên vật tư", "")).strip()
                ts = str(row.get("Thông số kỹ thuật", "")).strip()
                hang = str(row.get("Hãng sản xuất", "")).strip()
                
                cat = predict_category_fn(f"{ten} {ts}") if predict_category_fn else "Vật tư khác"
                
                writer.add_document(
                    **{
                        f.id_field: str(row.get("Mã vật tư", "")),
                        f.name_field: ten,
                        f.spec_field: ts,
                        f.brand_field: hang,
                        f.category_field: cat,
                        f.unit_field: str(row.get("ĐVT", "N/A")),
                        f.all_text_field: f"{ten} {ts} {hang}".strip().lower(),
                    }
                )
            writer.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi Build Index: {e}")
            return False

    def search(self, clean_query: str, limit: int = 60) -> List[Dict]:
        """Thực hiện tìm kiếm tầng 1 (Lexical)"""
        if not exists_in(self.index_dir): return []
        
        ix = open_dir(self.index_dir)
        f = self.fields
        candidates = []

        with ix.searcher() as searcher:
            # Factory(0.5) giúp cân bằng giữa việc khớp tất cả từ và khớp 1 vài từ
            og = OrGroup.factory(0.5) 
            parser = MultifieldParser(list(f.query_fields), ix.schema, group=og)
            query = parser.parse(clean_query)
            results = searcher.search(query, limit=limit)

            for hit in results:
                candidates.append({
                    "ma": hit.get(f.id_field, ""),
                    "ten": hit.get(f.name_field, ""),
                    "ts": hit.get(f.spec_field, ""),
                    "hang": hit.get(f.brand_field, ""),
                    "chung_loai": hit.get(f.category_field, "N/A"),
                    "dvt": hit.get(f.unit_field, "N/A"),
                    "all_text": hit.get(f.all_text_field, ""),
                    "w_score": float(hit.score),
                })
        return candidates
    def exists(self) -> bool:
        """
        Kiểm tra sự tồn tại của chỉ mục (index) Whoosh.
        Hàm này giúp Engine xác nhận đã có dữ liệu vật tư được nạp hay chưa.
        """
        from whoosh.index import exists_in
        
        # 1. Kiểm tra xem đường dẫn thư mục có tồn tại không
        if not os.path.exists(self.index_dir):
            return False
            
        # 2. Kiểm tra xem trong thư mục đó có các file index hợp lệ của Whoosh không
        # Hàm exists_in của Whoosh sẽ quét các file .toc (Table of Contents)
        try:
            if exists_in(self.index_dir):
                return True
            else:
                return False
        except Exception:
            # Nếu có lỗi xảy ra (ví dụ thư mục trống hoặc file hỏng)
            return False