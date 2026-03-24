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

        # Part numbers
        part_numbers = re.findall(r"[a-z0-9]{2,}(?:[-_/\.]?[a-z0-9]{2,})+", text_l)

        # DN / PN
        dn = re.findall(r"\bdn\s*\d+", text_l)
        pn = re.findall(r"\bpn\s*\d+", text_l)

        # 3D dims 40x50x25
        dims = re.findall(r"\d+\s*x\s*\d+\s*x\s*\d+", text_l)

        # Materials
        mats = []
        for mat in self.materials["materials"]:
            for alias in mat["aliases"]:
                if alias in text_l:
                    mats.append(mat["canonical"])

        # Important keywords (after mapping)
        keywords = [w for w in text_l.split() if len(w) > 3]

        return {
            "part_numbers": part_numbers,
            "dn": dn,
            "pn": pn,
            "dimensions": dims,
            "materials": mats,
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