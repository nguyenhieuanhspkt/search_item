# core/reranker.py
# Hybrid RRF Reranker for AI Thẩm định Vật tư
# ---------------------------------------------------------------
# Tính năng:
#   - Kết hợp điểm từ Semantic (FAISS), Exact Match, Material, Dimension
#   - RRF Fusion: Score_final = Σ weight_i / (k + rank_i)
#   - Giải thích (Explainability) theo từng feature
# ---------------------------------------------------------------

import os
import re
import yaml
import numpy as np


class Reranker:

    def __init__(self, config_path="config"):
        """
        Load weights và chuẩn bị các thông số cần thiết.
        """

        self.weights = self._load_yaml(os.path.join(config_path, "weights.yaml"))
        self.materials = self._load_yaml(os.path.join(config_path, "materials.yaml"))
        self.synonyms = self._load_yaml(os.path.join(config_path, "synonyms.yaml"))

        self.k = self.weights["rrf"]["k"]                       # RRF constant
        self.w_sem = self.weights["scoring"]["semantic_weight"]
        self.w_part = self.weights["scoring"]["part_number_boost"]
        self.w_mat = self.weights["scoring"]["material_boost"]
        self.w_dim = self.weights["scoring"]["dimension_boost"]
        self.w_kw = self.weights["scoring"]["keyword_boost"]


    # ---------------------------------------------------------------
    # YAML Loader
    # ---------------------------------------------------------------
    def _load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


    # ---------------------------------------------------------------
    # Extract part numbers, dimensions, materials from query
    # ---------------------------------------------------------------
    def extract_features(self, text: str):
        text_l = text.lower()

        # 1. Part numbers: Cải tiến Regex để bắt cả mã đơn giản (chỉ chữ và số)
        # Regex cũ của Hiếu hơi gắt, chỉ bắt mã có dấu gạch/chấm.
        # Regex mới: Bắt các chuỗi có cả chữ và số, dài từ 4 ký tự trở lên (tránh bắt nhầm từ thường)
        part_numbers = re.findall(r"[a-z0-9]{2,}(?:[-_/\.]?[a-z0-9]{2,})+", text_l)
        # Bổ sung thêm các mã hiệu kiểu dính liền (Vd: LHB66T)
        simple_codes = re.findall(r"\b(?=[a-z]*[0-9])(?=[0-9]*[a-z])[a-z0-9]{4,}\b", text_l)
        all_pns = list(set(part_numbers + simple_codes))

        # 2. Quy cách kỹ thuật (DN, PN, Kích thước)
        dn = re.findall(r"\bdn\s*\d+", text_l)
        pn = re.findall(r"\bpn\s*\d+", text_l)
        # Bắt thêm kích thước 2D (40x50) hoặc 3D (40x50x25)
        dims = re.findall(r"\d+\s*x\s*\d+(?:\s*x\s*\d+)?", text_l)

        # 3. Vật liệu (Giữ nguyên logic của Hiếu nhưng dùng set để tránh lặp)
        mats = set()
        for mat in self.materials.get("materials", []):
            for alias in mat["aliases"]:
                if f" {alias} " in f" {text_l} ": # Khớp chính xác từ để tránh bắt nhầm
                    mats.add(mat["canonical"])

        # 4. Từ khóa quan trọng (Keywords)
        # Loại bỏ các từ vô nghĩa (stop words) thường gặp trong vật tư
        stop_words = {'cho', 'của', 'với', 'dùng', 'loại', 'theo', 'mới', 'bản', 'vẽ'}
        keywords = [w for w in text_l.split() if len(w) > 2 and w not in stop_words]

        return {
            "part_numbers": all_pns,
            "dn": dn,
            "pn": pn,
            "dimensions": dims,
            "materials": list(mats),
            "keywords": keywords,
        }


    # ---------------------------------------------------------------
    # Compute feature-level boost score
    # ---------------------------------------------------------------
    def feature_score(self, query_feat, candidate_text):
        cand = candidate_text.lower()
        score = 0
        reasons = []

        # Part-number exact match
        for pn in query_feat["part_numbers"]:
            if pn in cand:
                score += self.w_part
                reasons.append(f"Khớp mã hiệu: {pn}")

        # Material match
        for m in query_feat["materials"]:
            if m in cand:
                score += self.w_mat
                reasons.append(f"Khớp vật liệu: {m}")

        # Dimension match
        for d in query_feat["dimensions"]:
            if d in cand:
                score += self.w_dim
                reasons.append(f"Khớp kích thước: {d}")

        # DN / PN match
        for dn in query_feat["dn"]:
            if dn in cand:
                score += self.w_dim
                reasons.append(f"Khớp DN: {dn}")

        for pn in query_feat["pn"]:
            if pn in cand:
                score += self.w_dim
                reasons.append(f"Khớp PN: {pn}")

        # Keyword boost
        for kw in query_feat["keywords"]:
            if kw in cand:
                score += self.w_kw

        return score, reasons


    # ---------------------------------------------------------------
    # RRF FUSION
    # ---------------------------------------------------------------
    def rrf_score(self, rank, weight):
        return weight / (self.k + rank)


    # ---------------------------------------------------------------
    # MAIN RERANK FUNCTION
    # ---------------------------------------------------------------
    def rerank(self, query: str, candidates: list):
        """
        query: normalized query string
        candidates: list of dict từ VectorStore.search:
                    [{"score": float, "metadata": {...}}, ...]
        """

        query_feat = self.extract_features(query)

        results = []

        for rank, item in enumerate(candidates):
            semantic_score = item["score"]  # FAISS score
            meta = item["metadata"]

            # Combine name + spec
            cand_text = f"{meta.get('Tên vật tư', '')} {meta.get('Thông số kỹ thuật', '')}"

            # Calculate feature-level scoring
            fscore, reasons = self.feature_score(query_feat, cand_text)

            # RRF fusion
            final_score = (
                self.rrf_score(rank + 1, self.w_sem) +  # semantic
                fscore                                    # feature boosts
            )

            results.append({
                "final_score": final_score,
                "semantic": semantic_score,
                "feature_score": fscore,
                "metadata": meta,
                "reasons": reasons
            })

        # Sort desc
        ranked = sorted(results, key=lambda x: x["final_score"], reverse=True)

        return ranked[0], ranked  # return best + full ranking for debugging