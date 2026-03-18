# search_item/back_end/core/scorers.py
from __future__ import annotations
import os
import numpy as np
import torch
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, List
from sentence_transformers import SentenceTransformer, CrossEncoder, util

# Import các hàm chuẩn hóa từ file helpers
try:
    from .helpers import normalize_cross_scores, normalize_cos_score
except ImportError:
    # Fallback dự phòng
    def normalize_cross_scores(s, is_logit): return 1/(1+np.exp(-s)) if is_logit else s
    def normalize_cos_score(s): return (s + 1) / 2

@dataclass
class BiEncoderConfig:
    model_name_or_path: str
    device: str = "cpu"
    batch_size: int = 16
    set_num_threads: Optional[int] = 2 

@dataclass
class CrossEncoderConfig:
    model_name_or_path: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    device: str = "cpu"
    batch_size: int = 16
    cross_is_logit: bool = True
    set_num_threads: Optional[int] = 2

class BiEncoder:
    def __init__(self, cfg: BiEncoderConfig):
        self.cfg = cfg
        if cfg.set_num_threads:
            try:
                torch.set_num_threads(int(cfg.set_num_threads))
            except: pass
        
        # Tải model AI (BGE-M3 hoặc SBERT)
        self.model = SentenceTransformer(cfg.model_name_or_path, device=cfg.device)

    def encode_query(self, text: str) -> torch.Tensor:
        """
        FIX LỖI: Encode 1 chuỗi query duy nhất.
        Hàm này cực kỳ quan trọng để engine.py gọi khi bắt đầu tìm kiếm.
        """
        if not text:
            return torch.empty((0,), device=self.cfg.device)
        
        with torch.no_grad():
            vec = self.model.encode(
                text,
                batch_size=1,
                convert_to_tensor=True,
                device=self.cfg.device,
                show_progress_bar=False
            )
        return vec

    def encode_texts(self, texts: Sequence[str]) -> torch.Tensor:
        """Encode danh sách nhiều văn bản (Document Candidates)."""
        if not texts: 
            return torch.empty((0, 0), device=self.cfg.device)
        
        with torch.no_grad():
            return self.model.encode(
                list(texts), 
                batch_size=self.cfg.batch_size, 
                convert_to_tensor=True, 
                show_progress_bar=False,
                device=self.cfg.device
            )

    def get_scores(self, query_vec: torch.Tensor, doc_vecs: torch.Tensor) -> np.ndarray:
        """Tính Cosine Similarity và chuẩn hóa về dải [0, 1]."""
        if doc_vecs.numel() == 0: 
            return np.zeros((0,), dtype=np.float32)
        
        with torch.no_grad():
            # util.cos_sim trả về (1, N), lấy [0] để thành (N,)
            if query_vec.dim() == 1:
                query_vec = query_vec.unsqueeze(0)
            
            sims = util.cos_sim(query_vec, doc_vecs)[0]
            sims_np = sims.cpu().numpy()
            
        return normalize_cos_score(sims_np)

class CrossReranker:
    def __init__(self, cfg: CrossEncoderConfig):
        self.cfg = cfg
        # Tải model Cross-Encoder (Thường là MiniLM)
        self.model = CrossEncoder(cfg.model_name_or_path, device=cfg.device)

    def score_pairs(self, pairs: Sequence[Tuple[str, str]]) -> np.ndarray:
        """Chấm điểm sâu từng cặp (Query, Document)."""
        if not pairs: 
            return np.zeros((0,), dtype=np.float32)
        
        with torch.no_grad():
            raw = self.model.predict(
                list(pairs), 
                batch_size=self.cfg.batch_size,
                show_progress_bar=False
            )
        
        raw_np = np.asarray(raw, dtype=np.float32)
        return normalize_cross_scores(raw_np, self.cfg.cross_is_logit)

# =========================
# High-level factory
# =========================

@dataclass
class Scorers:
    bi: BiEncoder
    cross: CrossReranker

def create_scorers(
    bi_model_path: str,
    cross_model_path: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    device: str = "cpu",
    bi_batch: int = 16,
    cross_batch: int = 16,
    cross_is_logit: bool = True,
    threads: Optional[int] = 2,
) -> Scorers:
    """Tạo bộ đôi sát thủ AI."""
    bi_cfg = BiEncoderConfig(
        model_name_or_path=bi_model_path,
        device=device,
        batch_size=bi_batch,
        set_num_threads=threads,
    )
    cross_cfg = CrossEncoderConfig(
        model_name_or_path=cross_model_path,
        device=device,
        batch_size=cross_batch,
        cross_is_logit=cross_is_logit,
        set_num_threads=threads,
    )
    return Scorers(bi=BiEncoder(bi_cfg), cross=CrossReranker(cross_cfg))