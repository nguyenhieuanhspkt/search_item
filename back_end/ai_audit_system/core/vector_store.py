# core/vector_store.py
# Author: Developer
# Vector Store Layer – FAISS Index (CPU)
# --------------------------------------------------------------------
# Chức năng:
#   - Nhúng vector ERP Master vào FAISS
#   - Lưu/Load index + metadata
#   - Tìm kiếm Top-K ứng viên với tốc độ mili-giây
# --------------------------------------------------------------------

import os
import json
import faiss
import numpy as np


class VectorStore:

    def __init__(self, metric: str = "cosine"):
        """
        Parameters:
            metric: "cosine" hoặc "l2"
        """

        if metric == "cosine":
            self.index = None             # FAISS IndexFlatIP
            self.metric_type = "cosine"
        else:
            self.index = None             # FAISS IndexFlatL2
            self.metric_type = "l2"

        self.metadata = []               # List of dict
        self.dim = None                  # Vector dimension


    # ----------------------------------------------------------------
    # BUILD INDEX
    # ----------------------------------------------------------------
    def build_index(self, vectors: np.ndarray, metadata: list):
        """
        vectors: np.ndarray shape (N, D)
        metadata: list of dictionaries (ERP thông tin)
        """

        if not isinstance(vectors, np.ndarray):
            raise ValueError("Vectors must be a numpy array")

        self.dim = vectors.shape[1]
        self.metadata = metadata

        if self.metric_type == "cosine":
            # Normalize vectors to unit length for cosine similarity
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / (norms + 1e-12)

            self.index = faiss.IndexFlatIP(self.dim)   # inner product
        else:
            self.index = faiss.IndexFlatL2(self.dim)

        # Add vectors to index
        self.index.add(vectors.astype(np.float32))


    # ----------------------------------------------------------------
    # SAVE INDEX + METADATA
    # ----------------------------------------------------------------
    def save(self, index_path: str, metadata_path: str):
        """
        Lưu FAISS index và metadata ra file.
        """

        if self.index is None:
            raise RuntimeError("Index is empty. Cannot save.")

        faiss.write_index(self.index, index_path)

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)


    # ----------------------------------------------------------------
    # LOAD INDEX + METADATA
    # ----------------------------------------------------------------
    def load(self, index_path: str, metadata_path: str):
        """
        Khôi phục mô hình từ ổ đĩa.
        """

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Cannot find index: {index_path}")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Cannot find metadata: {metadata_path}")

        self.index = faiss.read_index(index_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # FAISS không lưu dim trực tiếp -> đọc từ index
        self.dim = self.index.d


    # ----------------------------------------------------------------
    # SEARCH TOP-K
    # ----------------------------------------------------------------
    def search(self, query_vec: np.ndarray, top_k: int = 50):
        """
        query_vec: vector shape (D,)
        return: list of dict: [{score, metadata}, ...]
        """

        if self.index is None:
            raise RuntimeError("Index has not been built or loaded.")

        # chuẩn hóa query cho cosine
        if self.metric_type == "cosine":
            q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
        else:
            q = query_vec

        q = q.reshape(1, -1).astype(np.float32)

        scores, indices = self.index.search(q, top_k)

        out = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            out.append({
                "score": float(score),
                "metadata": self.metadata[idx]
            })

        return out
