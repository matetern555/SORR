from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ScorecardConfig(Base):
    """Model dla konfiguracji karty oceny (preset)"""
    __tablename__ = "scorecard_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)  # np. "SERVICE_DEFAULT", "SALES_PL"
    scorecard_type = Column(String(50), nullable=False)  # SERVICE, SALES, RETENTION, COLLECTIONS
    global_system_prompt = Column(Text, nullable=True)  # Globalny prompt AI
    
    # Frazy (JSON)
    required_phrases = Column(JSON, nullable=True)  # [{"phrase": "...", "penalty": -1}]
    forbidden_phrases = Column(JSON, nullable=True)  # [{"phrase": "...", "penalty": -3, "hard_fail_threshold": 60}]
    
    # Reguły (JSON) - IF-THEN
    rules = Column(JSON, nullable=True)  # [{"condition": "...", "action": "...", "value": 5}]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacje
    evaluations = relationship("Evaluation", back_populates="scorecard_config")

class PhraseMatch(Base):
    """Model dla dopasowań fraz w rozmowie"""
    __tablename__ = "phrase_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    phrase = Column(String(500), nullable=False)
    phrase_type = Column(String(20), nullable=False)  # "required" lub "forbidden"
    found = Column(Boolean, nullable=False)  # Czy fraza została znaleziona
    timestamp = Column(String(20), nullable=True)  # Gdzie została znaleziona
    speaker = Column(String(50), nullable=True)  # KONSULTANT lub KLIENT
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacja
    evaluation = relationship("Evaluation", back_populates="phrase_matches")

class RuleApplied(Base):
    """Model dla zastosowanych reguł"""
    __tablename__ = "rules_applied"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    rule_description = Column(String(500), nullable=False)  # Opis reguły
    applied = Column(Boolean, nullable=False)  # Czy reguła została zastosowana
    effect = Column(Float, nullable=True)  # Efekt reguły (punkty +/-)
    hard_fail_applied = Column(Boolean, default=False)  # Czy zastosowano hard-fail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacja
    evaluation = relationship("Evaluation", back_populates="rules_applied")

