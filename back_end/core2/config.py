from dataclasses import dataclass, field

@dataclass
class SearchWeights:
    keyword: float = 0.5
    vector: float = 0.5

@dataclass
class ScorerThresholds:
    exact_priority: float = 0.95
    accept: float = 0.72
    reject: float = 0.10  # Hạ từ 0.35 xuống 0.10 để thấy kết quả bị phạt
@dataclass
class SearchParams:
    top_k: int = 10

@dataclass
class Config:
    db_path: str = "core2/entities.db"
    use_wal: bool = True
    # Đảm bảo các biến này tồn tại để retriever gọi tới
    weights: SearchWeights = field(default_factory=SearchWeights)
    thresholds: ScorerThresholds = field(default_factory=ScorerThresholds)
    search: SearchParams = field(default_factory=SearchParams)