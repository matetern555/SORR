from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Schema dla cytatu
class Quote(BaseModel):
    speaker: str
    timestamp: Optional[str] = None
    text: str
    is_positive: bool = True
    
    class Config:
        from_attributes = True

# Schema dla oceny kategorii
class CategoryScore(BaseModel):
    category_name: str
    weight: float
    score: int
    points: float
    comment: Optional[str] = None
    quotes: List[Quote] = []
    
    class Config:
        from_attributes = True

# Schema dla sentymentu
class SentimentInfo(BaseModel):
    start: Optional[float] = None
    end: Optional[float] = None
    delta: Optional[float] = None
    quote: Optional[str] = None

# Schema dla końcowej oceny
class EvaluationResult(BaseModel):
    id: int
    transcription_id: int
    scorecard_type: str
    overall_score: float
    grade: Optional[str] = None
    client_sentiment: Optional[SentimentInfo] = None
    consultant_sentiment: Optional[SentimentInfo] = None
    final_comment: Optional[str] = None
    category_scores: List[CategoryScore] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schema dla tworzenia oceny
class EvaluationCreate(BaseModel):
    transcription_id: int
    scorecard_type: str = "SERVICE"

