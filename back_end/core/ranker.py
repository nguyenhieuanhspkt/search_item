# search_item/back_end/core/ranker.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any, List

from .config import RankConfig
from .helpers import clamp01


# ============================================================
# 1) Heuristic ranker: hợp điểm theo trọng số + bonus/penalty
# ============================================================

@dataclass
class HeuristicRanker:
    """
    Hợp điểm heuristic:
      final = w_cross*s_cross + w_bi*s_bi + w_lex*w_norm + bonus - penalty

    - Trọng số lấy từ RankConfig (đã validate tổng = 1.0).
    - Trả về (final, details) để phục vụ explain/debug ở Frontend.
    - 'rounded' cho phép làm tròn các thành phần để hiển thị gọn.

    Ví dụ sử dụng:
        ranker = HeuristicRanker(cfg)
        final, parts = ranker.score(s_cross=0.8, s_bi=0.7, w_norm=0.6, bonus=0.15, penalty=0.1)

    parts:
        {
          "weighted_cross": 0.36,
          "weighted_bi": 0.245,
          "weighted_lex": 0.12,
          "bonus": 0.15,
          "penalty": 0.1
        }
    """
    cfg: RankConfig

    def score(
        self,
        s_cross: float,
        s_bi: float,
        w_norm: float,
        bonus: float,
        penalty: float,
        rounded: int = 4
    ) -> Tuple[float, Dict[str, float]]:
        # Thành phần trọng số
        v_cross = self.cfg.w_cross * float(s_cross)
        v_bi    = self.cfg.w_bi    * float(s_bi)
        v_lex   = self.cfg.w_lex   * float(w_norm)

        # Tổng điểm & clamp
        final = v_cross + v_bi + v_lex + float(bonus) - float(penalty)
        final = clamp01(final)

        # Chi tiết để explain (Frontend hiển thị “vì saoDoc đứng top”)
        details = {
            "weighted_cross": round(v_cross,  rounded),
            "weighted_bi":    round(v_bi,     rounded),
            "weighted_lex":   round(v_lex,    rounded),
            "bonus":          round(float(bonus),   rounded),
            "penalty":        round(float(penalty), rounded),
        }
        return final, details

    # Nếu nơi nào đó chỉ cần 'float', có thể dùng hàm này để giữ tương thích ngược
    def score_value_only(
        self,
        s_cross: float,
        s_bi: float,
        w_norm: float,
        bonus: float,
        penalty: float,
    ) -> float:
        final, _ = self.score(s_cross, s_bi, w_norm, bonus, penalty)
        return final


# ============================================================
# 2) ML ranker (skeleton): để gắn Learning-to-Rank sau này
# ============================================================

class MLRanker:
    """
    Skeleton cho Learning-to-Rank (LTR).
    - Nhận dict features (ví dụ: s_cross, s_bi, w_norm, bonus, penalty, match_ratio, code_hit, spec_hit,...)
    - Chuyển thành vector theo feature_map
    - Gọi model.predict_proba / predict
    - Trả về (final, details) với thêm thông tin mô hình

    Lưu ý:
      - Bạn cần tự quản lý chuẩn hoá features (min-max hoặc z-score) nhất quán giữa huấn luyện & infer.
      - model có thể là LogisticRegression/LightGBM/XGBoost... (được nạp từ joblib/pickle).
    """

    def __init__(
        self,
        model: Any,
        feature_map: Optional[Dict[str, int]] = None,
        model_name: str = "LTRModel",
        proba_index: int = 1
    ) -> None:
        """
        Args:
          model        : đối tượng đã load (joblib/pickle)
          feature_map  : mapping tên feature -> index trong vector (đảm bảo cố định với lúc train)
          model_name   : tên hiển thị phục vụ explain/log
          proba_index  : nếu sử dụng predict_proba, lấy cột nào (mặc định lấy proba lớp 1)
        """
        self.model = model
        self.feature_map = feature_map or {}
        self.model_name = model_name
        self.proba_index = int(proba_index)

    # ---------- private ----------

    def _to_vector(self, features: Dict[str, float]) -> List[float]:
        """
        Biến dict feature -> vector [x1, x2, ...] theo thứ tự feature_map.
        Giá trị feature không có trong mapping sẽ bị bỏ qua (coi như 0.0).
        """
        vec = [0.0] * len(self.feature_map)
        for k, idx in self.feature_map.items():
            vec[idx] = float(features.get(k, 0.0))
        return vec

    def _predict_score(self, vec: List[float]) -> float:
        """
        Gọi model để lấy score (∈ [0,1] nếu có predict_proba; nếu predict -> tự clamp).
        """
        try:
            # Scikit-learn-like
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba([vec])[0]
                # Lấy cột proba_index (mặc định lớp 1)
                score = float(proba[self.proba_index])
            elif hasattr(self.model, "predict"):
                score = float(self.model.predict([vec])[0])
            else:
                # Không có API quen thuộc -> fallback
                score = 0.5
        except Exception:
            score = 0.5

        return clamp01(score)

    # ---------- public ----------

    def score(
        self,
        features: Dict[str, float],
        rounded: int = 4
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Args:
          features : dict các đặc trưng đã được chuẩn hoá đúng với lúc train LTR.

        Returns:
          (final, details)
            - final   : điểm cuối ∈ [0,1]
            - details :
                {
                  "model": "LightGBMRanker@v0.3",
                  "score_raw": 0.8123,
                  "top_features": ["s_cross", "code_hit", "match_ratio"]  # nếu có
                }
        """
        vec = self._to_vector(features)
        score = self._predict_score(vec)

        details: Dict[str, Any] = {
            "model": self.model_name,
            "score_raw": round(score, rounded)
        }

        # Nếu model có thuộc tính feature_importances_ (LightGBM/XGB), có thể trả top-k feature
        try:
            import numpy as np  # cục bộ để giảm phụ thuộc
            if hasattr(self.model, "feature_importances_"):
                imps = getattr(self.model, "feature_importances_")
                imps = list(imps)  # list[float]
                # Lấy top 3 feature quan trọng (tuỳ chọn)
                pairs = sorted(self.feature_map.items(), key=lambda kv: imps[kv[1]], reverse=True)
                top_feats = [name for name, _ in pairs[:3]]
                details["importance_top"] = top_feats
        except Exception:
            pass

        return score, details