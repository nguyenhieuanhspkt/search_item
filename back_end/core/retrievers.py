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

    # Sửa lại hàm trong class WhooshRetriever
    def build_index_from_dataframe(
        self, 
        df: pd.DataFrame, 
        categories_list: Optional[List[str]] = None, 
        overwrite: bool = True
    ) -> bool:
        """
        Xây dựng Index Whoosh từ DataFrame. 
        Sử dụng danh sách chủng loại đã được dự đoán trước (Batch) để tối ưu tốc độ.
        """
        import os
        from whoosh.index import create_in

        try:
            # 1. Chuẩn bị thư mục index
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)

            # 2. Kiểm tra tính hợp lệ của dữ liệu đầu vào
            if categories_list and len(categories_list) != len(df):
                print(f"⚠️ Cảnh báo: Danh sách chủng loại ({len(categories_list)}) "
                      f"không khớp với số dòng dữ liệu ({len(df)}).")
                # Nếu không khớp, ta sẽ bù bằng "Vật tư khác" để tránh lỗi index out of range
                if len(categories_list) < len(df):
                    categories_list.extend(["Vật tư khác"] * (len(df) - len(categories_list)))

            # 3. Khởi tạo Index và Writer
            ix = create_in(self.index_dir, self.schema())
            
            # limitmb=512 giúp Whoosh sử dụng nhiều RAM hơn để giảm số lần ghi đĩa (I/O)
            # procs=2 (tùy chọn) có thể dùng để chạy đa tiến trình nếu file cực lớn
            writer = ix.writer(limitmb=512) 

            f = self.fields
            print(f"--- ✍️ Đang ghi {len(df)} tài liệu vào Index ---")

            # 4. Lặp và thêm tài liệu
            for i, (_, row) in enumerate(df.iterrows()):
                # Trích xuất và làm sạch dữ liệu từ row
                ma_vattu = str(row.get("Mã vật tư", "")).strip()
                ten_vattu = str(row.get("Tên vật tư", "")).strip()
                thong_so = str(row.get("Thông số kỹ thuật", "")).strip()
                hang_sx = str(row.get("Hãng sản xuất", "")).strip()
                dvt = str(row.get("ĐVT", "N/A")).strip()
                
                # Ưu tiên lấy từ categories_list (đã chạy Batch AI từ trước)
                cat = categories_list[i] if categories_list else "Vật tư khác"
                
                # Tạo trường all_text để tìm kiếm toàn văn (lexical search)
                # Chuyển về chữ thường để Whoosh tìm kiếm không phân biệt hoa thường hiệu quả hơn
                combined_text = f"{ten_vattu} {thong_so} {hang_sx}".strip().lower()

                writer.add_document(
                    **{
                        f.id_field: ma_vattu,
                        f.name_field: ten_vattu,
                        f.spec_field: thong_so,
                        f.brand_field: hang_sx,
                        f.category_field: cat,
                        f.unit_field: dvt,
                        f.all_text_field: combined_text,
                    }
                )

            # 5. Lưu thay đổi
            print("--- 💾 Đang commit dữ liệu xuống ổ đĩa (vui lòng đợi)... ---")
            writer.commit()
            print("--- ✅ Build Index hoàn tất thành công! ---")
            return True

        except Exception as e:
            # Nếu có lỗi, cố gắng hủy bỏ các thay đổi chưa commit để tránh hỏng index
            if 'writer' in locals():
                writer.cancel()
            print(f"❌ Lỗi nghiêm trọng khi Build Index: {str(e)}")
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