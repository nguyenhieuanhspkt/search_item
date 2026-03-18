# search_item/back_end/core/rules.py
from __future__ import annotations

import re
from typing import List, Tuple, Dict, Any, Optional

from .helpers import has_token, numbers_match_ratio


class BusinessRules:
    """
    Bộ quy tắc nghiệp vụ áp dụng cho một cặp (query, document):
    - Thưởng khi khớp mã hiệu kỹ thuật (code) theo boundary.
    - Thưởng khi khớp chuỗi 'số + đơn vị' (spec) đã trích trước đó.
    - Thưởng theo tỉ lệ khớp số đo; phạt khi mismatch (0 hoặc < 0.5).
    - Phạt các xung đột nghiệp vụ (sealant vs van, HCl vs NaOH, ...).
    - Áp trần bonus/penalty để không 'đè' điểm mô hình.

    Bạn có thể mở rộng nhanh bằng cách thêm rule vào _apply_custom_rules().
    """

    def __init__(
        self,
        cap_bonus: float = 0.40,
        cap_penalty: float = 0.60,
        # Hệ số thưởng/phạt có thể cấu hình tuỳ domain:
        code_bonus: float = 0.15,
        spec_bonus: float = 0.10,
        num_bonus_scale: float = 0.20,  # bonus += ratio * scale
        num_penalty_zero: float = 0.35, # ratio == 0
        num_penalty_low: float = 0.15,  # ratio < 0.5
        conflict_rules: Optional[List[Tuple[str, str, float]]] = None,
    ):
        self.cap_bonus = cap_bonus
        self.cap_penalty = cap_penalty
        self.code_bonus = code_bonus
        self.spec_bonus = spec_bonus
        self.num_bonus_scale = num_bonus_scale
        self.num_penalty_zero = num_penalty_zero
        self.num_penalty_low = num_penalty_low

        # conflict_rules: list các cặp (token_query, token_doc, penalty)
        # VD mặc định: [("sealant","van",0.4), ("hcl","naoh",0.6)]
        self.conflict_rules = conflict_rules or [
            ("sealant", "van", 0.40),
            ("hcl", "naoh", 0.60),
        ]

    # ---------- Public API ----------

    def compute_bonus_penalty(
        self,
        query_str: str,
        doc_text: str,
        q_codes: List[str],
        q_specs: List[str],
        q_numbers: List[str],
        explain: bool = False
    ) -> Tuple[float, float, List[str]]:
        """
        Tính tổng bonus/penalty cho 1 cặp (query, doc).
        Trả về: (bonus, penalty, reasons)
        """
        q_low = query_str.lower()
        doc_low = doc_text.lower()
        doc_up  = doc_text.upper()

        bonus = 0.0
        penalty = 0.0
        reasons: List[str] = []

        # 1) Thưởng khi khớp mã hiệu (word boundary + UPPER)
        for code in q_codes:
            code_up = code.upper().strip()
            if len(code_up) > 2 and re.search(rf'\b{re.escape(code_up)}\b', doc_up):
                bonus += self.code_bonus
                if explain:
                    reasons.append(f"+code:{code_up}")

        # 2) Thưởng spec 'số + đơn vị'
        for spec in q_specs:
            if spec.lower() in doc_low:
                bonus += self.spec_bonus
                if explain:
                    reasons.append(f"+spec:{spec}")

        # 3) Thưởng/phạt theo tỉ lệ khớp số đo
        if q_numbers:
            ratio = numbers_match_ratio(q_numbers, doc_low)
            bonus += (ratio * self.num_bonus_scale)

            if ratio == 0:
                penalty += self.num_penalty_zero
            elif ratio < 0.5:
                penalty += self.num_penalty_low

            if explain:
                reasons.append(f"+num_ratio:{ratio:.2f}")

        # 4) Phạt xung đột nghiệp vụ chuẩn hoá bằng boundary
        for q_tok, d_tok, p_val in self.conflict_rules:
            if has_token(q_tok, q_low) and has_token(d_tok, doc_low):
                penalty += float(p_val)
                if explain:
                    reasons.append(f"-biz:{q_tok}_vs_{d_tok}")

        # 5) Rule tuỳ chỉnh khác (mở rộng tại đây)
        bonus, penalty, reasons = self._apply_custom_rules(
            query_str=query_str,
            doc_text=doc_text,
            bonus=bonus,
            penalty=penalty,
            reasons=reasons,
            explain=explain,
        )

        # 6) Capping
        if bonus > self.cap_bonus:
            bonus = self.cap_bonus
        if penalty > self.cap_penalty:
            penalty = self.cap_penalty

        return bonus, penalty, reasons

    # ---------- Extension point ----------

    def _apply_custom_rules(
        self,
        query_str: str,
        doc_text: str,
        bonus: float,
        penalty: float,
        reasons: List[str],
        explain: bool
    ) -> Tuple[float, float, List[str]]:
        """
        Đặt thêm quy tắc tuỳ domain tại đây.
        Ví dụ:
          - Ưu tiên hãng cụ thể (nếu query có '3M', doc chứa '3M' -> +0.05).
          - Ưu tiên chủng loại đúng (cat) nếu bạn đưa cat vào doc_text/all_text.
        """
        # Ví dụ minh hoạ (comment sẵn):
        # q_low = query_str.lower()
        # d_low = doc_text.lower()
        # if "3m" in q_low and "3m" in d_low:
        #     bonus += 0.05
        #     if explain: reasons.append("+brand:3m")
        return bonus, penalty, reasons