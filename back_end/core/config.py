# search_item/back_end/core/config.py
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import os

@dataclass
class RankConfig:
    """
    Hệ thống cấu hình xếp hạng Hybrid Search cho Vĩnh Tân 4.
    - Quản lý trọng số giữa AI (Semantic) và Từ khóa (Lexical).
    - Thiết lập các ngưỡng phạt/thưởng để chống lỗi "100% ảo".
    """

    # --- 1) TRỌNG SỐ HỢP ĐIỂM (Tổng phải bằng 1.0) ---
    w_cross: float = 0.45  # Trọng số Cross-Encoder (Hiểu ngữ nghĩa sâu)
    w_bi: float = 0.35     # Trọng số Bi-Encoder (BGE-M3 - Bao quát ý nghĩa)
    w_lex: float = 0.20    # Trọng số Lexical (Whoosh - Khớp từ khóa/mã chính xác)

    # --- 2) NGƯỠNG THƯỞNG / PHẠT (Capping) ---
    cap_bonus: float = 0.40   # Thưởng tối đa (không cho phép vượt quá 40% điểm cộng thêm)
    cap_penalty: float = 0.60 # Phạt tối đa (tránh việc điểm bị âm quá sâu)

    # --- 3) CẤU HÌNH MÔ HÌNH & RECALL ---
    cross_is_logit: bool = True  # True nếu model trả về logit (cần Sigmoid)
    whoosh_limit: int = 60       # Số lượng ứng viên lấy ra từ tầng 1
    rerank_top_n: int = 30       # Số lượng ứng viên đưa vào Re-ranking (tầng 2 & 3)

    # --- 4) QUẢN TRỊ PHIÊN BẢN ---
    version: str = "1.1.0"

    def __post_init__(self) -> None:
        """Tự động kiểm tra tính hợp lệ của thông số ngay khi khởi tạo"""
        # Kiểm tra dải điểm [0, 1]
        for name, v in (("w_cross", self.w_cross), ("w_bi", self.w_bi), ("w_lex", self.w_lex)):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"Lỗi: {name} phải nằm trong khoảng [0, 1], hiện tại là {v}")

        # Kiểm tra tổng trọng số (cho phép sai số float rất nhỏ)
        total = self.w_cross + self.w_bi + self.w_lex
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Lỗi: Tổng trọng số w_cross + w_bi + w_lex phải bằng 1.0, hiện tại là {total:.6f}")

        # Kiểm tra tính logic của phễu lọc
        if self.rerank_top_n > self.whoosh_limit:
            raise ValueError(f"Lỗi: rerank_top_n ({self.rerank_top_n}) không được lớn hơn whoosh_limit ({self.whoosh_limit})")

    # --- CÁC PHƯƠNG THỨC TIỆN ÍCH (HELPER METHODS) ---

    def save(self, file_path: str):
        """Lưu cấu hình ra file JSON để Admin chỉnh sửa nhanh"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            print(f"--- ✅ Đã lưu cấu hình mới vào: {file_path} ---")
        except Exception as e:
            print(f"--- ❌ Lỗi khi lưu file config: {e} ---")

    @classmethod
    def load(cls, file_path: str) -> "RankConfig":
        """Nạp cấu hình từ file, nếu không có hoặc lỗi thì dùng mặc định"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"--- ⚠️ Lỗi đọc file config, dùng mặc định: {e} ---")
        return cls()

    # --- CÁC PRESETS (CẤU HÌNH SẴN) ---

    @classmethod
    def numeric_heavy(cls) -> "RankConfig":
        """Cấu hình ưu tiên độ chính xác của từ khóa và số liệu (Dành cho vật tư cơ khí)"""
        return cls(w_cross=0.30, w_bi=0.20, w_lex=0.50, cap_penalty=0.80)

    @classmethod
    def semantic_heavy(cls) -> "RankConfig":
        """Cấu hình ưu tiên tìm theo ý nghĩa (Dành cho vật tư khó gọi tên chuẩn)"""
        return cls(w_cross=0.50, w_bi=0.40, w_lex=0.10, cap_bonus=0.50)