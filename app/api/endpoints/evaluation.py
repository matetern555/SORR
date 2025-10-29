from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ...database import get_db
from ...models.transcription import Transcription
from ...models.speaker_segment import SpeakerSegment
from ...models.evaluation import Evaluation, CategoryScore, Quote
from ...models.scorecard import PhraseMatch, RuleApplied
from ...models.audio import AudioFile
from ...schemas.evaluation import EvaluationResult, EvaluationCreate
from pydantic import BaseModel
from ...services.evaluation import evaluate_conversation
from ...services.rules_engine import (
    find_phrases_in_transcription,
    apply_required_phrases_penalty,
    apply_forbidden_phrases_penalty,
    apply_rules,
    apply_hard_fail_threshold,
    get_default_service_scorecard
)

router = APIRouter()

@router.post("/evaluate/{transcription_id}", response_model=EvaluationResult)
def evaluate_transcription(
    transcription_id: int,
    scorecard_type: str = "SERVICE",
    db: Session = Depends(get_db)
):
    """
    Ocenia rozmowę używając karty oceny (SERVICE).
    """
    try:
        print(f"Rozpoczynanie oceny transkrypcji ID: {transcription_id}")
        
        # Sprawdź czy transkrypcja istnieje
        transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
        if not transcription:
            raise HTTPException(status_code=404, detail="Transkrypcja nie znaleziona")
        
        # Sprawdź czy są segmenty mówców
        speaker_segments = db.query(SpeakerSegment).filter(
            SpeakerSegment.transcription_id == transcription_id
        ).order_by(SpeakerSegment.start_time).all()
        
        if not speaker_segments:
            raise HTTPException(
                status_code=400,
                detail="Brak segmentów mówców. Najpierw wykonaj diaryzację."
            )
        
        print(f"Znaleziono {len(speaker_segments)} segmentów mówców")
        
        # Sprawdź czy ocena już istnieje
        existing_evaluation = db.query(Evaluation).options(
            joinedload(Evaluation.category_scores)
        ).filter(
            Evaluation.transcription_id == transcription_id
        ).first()
        
        if existing_evaluation:
            # Zwróć istniejącą ocenę
            print("Zwracam istniejącą ocenę")
            return existing_evaluation
        
        # Wykonaj ocenę przez GPT-4
        print("Wykonywanie oceny przez GPT-4...")
        evaluation_result = evaluate_conversation(
            transcription_text=transcription.text or "",
            speaker_segments=speaker_segments
        )
        
        base_score = evaluation_result["overall_score"]
        print(f"Wynik bazowy: {base_score}%")
        
        # Zastosuj Rules Engine (frazy i reguły)
        print("Zastosowuję Rules Engine...")
        scorecard_config = get_default_service_scorecard()
        
        # Znajdź frazy obowiązkowe
        required_phrases = scorecard_config.get("required_phrases", [])
        required_matches = find_phrases_in_transcription(
            transcription.text or "",
            [{"text": s.text, "start_time": s.start_time, "speaker_label": s.speaker_label} 
             for s in speaker_segments],
            required_phrases
        )
        
        # Zastosuj kary za brak fraz obowiązkowych
        adjusted_score, required_adjustments = apply_required_phrases_penalty(base_score, required_matches)
        print(f"Po frazach obowiązkowych: {adjusted_score}%")
        
        # Znajdź frazy zakazane
        forbidden_phrases = scorecard_config.get("forbidden_phrases", [])
        forbidden_matches = find_phrases_in_transcription(
            transcription.text or "",
            [{"text": s.text, "start_time": s.start_time, "speaker_label": s.speaker_label} 
             for s in speaker_segments],
            forbidden_phrases
        )
        
        # Zastosuj kary za użycie fraz zakazanych
        adjusted_score, hard_fail_threshold, forbidden_adjustments = apply_forbidden_phrases_penalty(
            adjusted_score, forbidden_matches
        )
        print(f"Po frazach zakazanych: {adjusted_score}%")
        
        # Zastosuj reguły IF-THEN (uproszczone)
        rules = scorecard_config.get("rules", [])
        adjusted_score, applied_rules = apply_rules(
            adjusted_score,
            transcription.text or "",
            [{"text": s.text, "start_time": s.start_time, "speaker_label": s.speaker_label} 
             for s in speaker_segments],
            rules
        )
        print(f"Po regułach (uproszczone): {adjusted_score}%")
        
        # Zastosuj hard-fail (sufit)
        if hard_fail_threshold:
            adjusted_score = apply_hard_fail_threshold(adjusted_score, hard_fail_threshold)
            print(f"Po hard-fail (max {hard_fail_threshold}%): {adjusted_score}%")
        
        # Przelicz ocenę literową po wszystkich zmianach
        from ...services.evaluation import calculate_grade
        final_grade = calculate_grade(adjusted_score)
        
        # Zapisz ocenę w bazie danych
        evaluation = Evaluation(
            transcription_id=transcription_id,
            scorecard_type=scorecard_type,
            base_score=base_score,
            overall_score=adjusted_score,
            rules_adjustment=adjusted_score - base_score,
            grade=final_grade,
            final_comment=evaluation_result["final_comment"],
            hard_fail_applied=hard_fail_threshold is not None,
            hard_fail_threshold=hard_fail_threshold
        )
        
        db.add(evaluation)
        db.flush()  # Otrzymaj ID
        
        # Zapisz dopasowania fraz
        for match in required_matches + forbidden_matches:
            phrase_match = PhraseMatch(
                evaluation_id=evaluation.id,
                phrase=match["phrase"],
                phrase_type="required" if match in required_matches else "forbidden",
                found=match["found"],
                timestamp=match.get("timestamp"),
                speaker=match.get("speaker")
            )
            db.add(phrase_match)
        
        # Zapisz zastosowane reguły
        for rule in applied_rules:
            rule_applied = RuleApplied(
                evaluation_id=evaluation.id,
                rule_description=rule["description"],
                applied=rule["applied"],
                effect=rule.get("effect"),
                hard_fail_applied=rule.get("hard_fail_threshold") is not None
            )
            db.add(rule_applied)
        
        # Usuń stare kategorie jeśli istnieją (zabezpieczenie przed duplikatami)
        existing_categories = db.query(CategoryScore).filter(
            CategoryScore.evaluation_id == evaluation.id
        ).all()
        
        for existing_cat in existing_categories:
            # Usuń też cytaty związane z kategorią
            db.query(Quote).filter(
                Quote.category_score_id == existing_cat.id
            ).delete()
            db.delete(existing_cat)
        
        db.flush()
        
        # Zapisz kategorie (tylko unikalne)
        seen_categories = set()
        for cat_result in evaluation_result["category_results"]:
            category_name = cat_result["name"]
            
            # Pomiń duplikaty w tej samej ocenie
            if category_name in seen_categories:
                print(f"Pomijam duplikat kategorii: {category_name}")
                continue
            
            seen_categories.add(category_name)
            
            category_score = CategoryScore(
                evaluation_id=evaluation.id,
                category_name=category_name,
                weight=cat_result["weight"],
                score=cat_result["score"],
                points=cat_result["weight"] * (cat_result["score"] / 5.0),
                comment=cat_result["comment"]
            )
            db.add(category_score)
            db.flush()
            
            # Zapisz cytaty
            for quote_data in cat_result.get("quotes", []):
                quote = Quote(
                    category_score_id=category_score.id,
                    speaker=quote_data.get("speaker", ""),
                    timestamp=quote_data.get("timestamp"),
                    text=quote_data.get("text", ""),
                    is_positive=quote_data.get("is_positive", True)
                )
                db.add(quote)
        
        db.commit()
        db.refresh(evaluation)
        
        # Załaduj pełną ocenę z kategoriami i cytatami
        evaluation = db.query(Evaluation).options(
            joinedload(Evaluation.category_scores).joinedload(CategoryScore.quotes)
        ).filter(Evaluation.id == evaluation.id).first()
        
        print(f"Ocena zapisana: {evaluation.overall_score}% (Grade: {evaluation.grade})")
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Błąd podczas oceny: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas oceny rozmowy: {str(e)}"
        )

@router.get("/evaluations/{transcription_id}", response_model=EvaluationResult)
def get_evaluation(
    transcription_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera ocenę dla danej transkrypcji.
    """
    evaluation = db.query(Evaluation).options(
        joinedload(Evaluation.category_scores).joinedload(CategoryScore.quotes)
    ).filter(
        Evaluation.transcription_id == transcription_id
    ).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail="Ocena nie znaleziona"
        )
    
    return evaluation

@router.get("/evaluations/", response_model=List[EvaluationResult])
def list_evaluations(db: Session = Depends(get_db)):
    """
    Lista wszystkich ocen.
    """
    return db.query(Evaluation).all()

class ConversationHistory(BaseModel):
    """Pełna historia rozmowy z wszystkimi danymi"""
    audio_id: int
    audio_filename: str
    audio_created_at: str
    transcription_id: int
    transcription_text: Optional[str] = None
    evaluation_id: Optional[int] = None
    evaluation_score: Optional[float] = None
    evaluation_grade: Optional[str] = None
    evaluation_created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/conversations/history", response_model=List[ConversationHistory])
def get_conversations_history(db: Session = Depends(get_db)):
    """
    Zwraca pełną historię wszystkich rozmów z wszystkimi danymi.
    """
    try:
        # Pobierz wszystkie pliki audio z transkrypcjami
        audio_files = db.query(AudioFile).order_by(AudioFile.created_at.desc()).all()
        
        history = []
        for audio in audio_files:
            # Znajdź transkrypcję
            transcription = db.query(Transcription).filter(
                Transcription.audio_file_id == audio.id
            ).first()
            
            if transcription:
                # Znajdź ocenę
                evaluation = db.query(Evaluation).filter(
                    Evaluation.transcription_id == transcription.id
                ).first()
                
                history.append(ConversationHistory(
                    audio_id=audio.id,
                    audio_filename=audio.filename or "Nieznany plik",
                    audio_created_at=audio.created_at.isoformat() if audio.created_at else "",
                    transcription_id=transcription.id,
                    transcription_text=transcription.text or None,
                    evaluation_id=evaluation.id if evaluation else None,
                    evaluation_score=evaluation.overall_score if evaluation else None,
                    evaluation_grade=evaluation.grade if evaluation else None,
                    evaluation_created_at=evaluation.created_at.isoformat() if evaluation and evaluation.created_at else None
                ))
        
        return history
    except Exception as e:
        import traceback
        print(f"Błąd w get_conversations_history: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania historii: {str(e)}")

