from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Evaluation(Base):
    """Model dla głównej oceny rozmowy"""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), nullable=False)
    scorecard_type = Column(String(50), nullable=False)  # SERVICE, SALES, RETENTION, COLLECTIONS
    scorecard_config_id = Column(Integer, ForeignKey("scorecard_configs.id"), nullable=True)  # Preset użyty
    overall_score = Column(Float, nullable=False)  # Wynik 0-100
    base_score = Column(Float, nullable=True)  # Wynik przed regułami
    rules_adjustment = Column(Float, nullable=True)  # Suma zmian z reguł
    grade = Column(String(10), nullable=True)  # A, B, C, D
    final_comment = Column(Text, nullable=True)  # Komentarz końcowy AI
    hard_fail_applied = Column(Boolean, default=False)  # Czy zastosowano hard-fail
    hard_fail_threshold = Column(Float, nullable=True)  # Sufit wyniku
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacje
    transcription = relationship("Transcription", back_populates="evaluations")
    scorecard_config = relationship("ScorecardConfig", back_populates="evaluations")
    category_scores = relationship("CategoryScore", back_populates="evaluation", cascade="all, delete-orphan")
    phrase_matches = relationship("PhraseMatch", back_populates="evaluation", cascade="all, delete-orphan")
    rules_applied = relationship("RuleApplied", back_populates="evaluation", cascade="all, delete-orphan")

class CategoryScore(Base):
    """Model dla oceny pojedynczej kategorii"""
    __tablename__ = "category_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    category_name = Column(String(200), nullable=False)
    weight = Column(Float, nullable=False)  # Waga w procentach
    score = Column(Integer, nullable=False)  # Ocena 1-5
    points = Column(Float, nullable=False)  # Punkty = (score/5) * weight
    comment = Column(Text, nullable=True)  # Komentarz AI
    
    # Relacje
    evaluation = relationship("Evaluation", back_populates="category_scores")
    quotes = relationship("Quote", back_populates="category_score", cascade="all, delete-orphan")

class Quote(Base):
    """Model dla cytatów (dowodów) z kategorii"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    category_score_id = Column(Integer, ForeignKey("category_scores.id"), nullable=False)
    speaker = Column(String(50), nullable=False)  # KONSULTANT lub KLIENT
    timestamp = Column(String(20), nullable=True)  # Format HH:MM:SS
    text = Column(Text, nullable=False)
    is_positive = Column(Boolean, default=True)  # Czy pozytywny czy negatywny cytat
    
    # Relacja
    category_score = relationship("CategoryScore", back_populates="quotes")

# Dodajemy relację do modelu Transcription
from .transcription import Transcription
Transcription.evaluations = relationship("Evaluation", back_populates="transcription", cascade="all, delete-orphan")

# Importujemy nowe modele
from .scorecard import ScorecardConfig, PhraseMatch, RuleApplied

