from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Candidate:
    raw_text: str
    normalized: str
    type_hint: Optional[str] = None  # 'model', 'brand', 'text'
    meta: Optional[Dict[str, Any]] = None

@dataclass
class ScoredModel:
    model_code: str
    brand: Optional[str]
    score: float
    priority_pass: bool
    reasons: List[str] = field(default_factory=list)
    extra: Optional[Dict[str, Any]] = None

@dataclass
class RetrievalHit:
    product_id: int
    model_code: str
    brand: str
    name: str
    score_keyword: float = 0.0
    score_vector: float = 0.0
    combined: float = 0.0
    reasons: List[str] = field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None

@dataclass
class ValidationIssue:
    code: str
    message: str
    penalty: float

@dataclass
class EngineResult:
    input_text: str
    candidates: List[Candidate]
    primary_model: Optional[ScoredModel]
    hits: List[RetrievalHit]
    issues: List[ValidationIssue]
    final_score: float
    selected_product_id: Optional[int] = None