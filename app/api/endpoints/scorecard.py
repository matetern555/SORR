from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ...database import get_db
from ...models.scorecard import ScorecardConfig
from ...services.rules_engine import get_default_service_scorecard

router = APIRouter()

class ScorecardConfigCreate(BaseModel):
    name: str
    scorecard_type: str
    global_system_prompt: str = None
    required_phrases: List[str] = []
    forbidden_phrases: List[str] = []
    rules: List[dict] = []

class ScorecardConfigResponse(BaseModel):
    id: int
    name: str
    scorecard_type: str
    global_system_prompt: str = None
    required_phrases: List[str] = []
    forbidden_phrases: List[str] = []
    rules: List[dict] = []
    
    class Config:
        from_attributes = True

@router.post("/scorecards/", response_model=ScorecardConfigResponse)
def create_scorecard(
    scorecard_data: ScorecardConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Tworzy nową kartę oceny (preset).
    """
    # Sprawdź czy nazwa już istnieje
    existing = db.query(ScorecardConfig).filter(
        ScorecardConfig.name == scorecard_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Karta o nazwie '{scorecard_data.name}' już istnieje"
        )
    
    scorecard = ScorecardConfig(
        name=scorecard_data.name,
        scorecard_type=scorecard_data.scorecard_type,
        global_system_prompt=scorecard_data.global_system_prompt,
        required_phrases=scorecard_data.required_phrases,
        forbidden_phrases=scorecard_data.forbidden_phrases,
        rules=scorecard_data.rules
    )
    
    db.add(scorecard)
    db.commit()
    db.refresh(scorecard)
    
    return scorecard

@router.get("/scorecards/", response_model=List[ScorecardConfigResponse])
def list_scorecards(db: Session = Depends(get_db)):
    """
    Zwraca listę wszystkich kart oceny.
    """
    return db.query(ScorecardConfig).all()

@router.get("/scorecards/{scorecard_id}", response_model=ScorecardConfigResponse)
def get_scorecard(
    scorecard_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera konkretną kartę oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(
            status_code=404,
            detail="Karta oceny nie znaleziona"
        )
    
    return scorecard

@router.get("/scorecards/default/service", response_model=ScorecardConfigResponse)
def get_default_service_scorecard_endpoint():
    """
    Zwraca domyślną kartę SERVICE z frazami i regułami.
    """
    default_config = get_default_service_scorecard()
    
    # Zwróć jako ScorecardConfigResponse
    return ScorecardConfigResponse(
        id=0,  # Nie jest zapisane w bazie
        name=default_config["name"],
        scorecard_type=default_config["scorecard_type"],
        required_phrases=default_config.get("required_phrases", []),
        forbidden_phrases=default_config.get("forbidden_phrases", []),
        rules=default_config.get("rules", [])
    )

# ========== PANEL ZARZĄDZANIA FRAZAMI ==========

class PhraseUpdate(BaseModel):
    """Model do aktualizacji fraz"""
    phrases: List[str]

@router.get("/scorecards/{scorecard_id}/phrases/required")
def get_required_phrases(
    scorecard_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera listę fraz obowiązkowych dla danej karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    # Jeśli to domyślna karta SERVICE, zwróć z kodu
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        default_config = get_default_service_scorecard()
        return {"phrases": default_config.get("required_phrases", [])}
    
    return {"phrases": scorecard.required_phrases or []}

@router.get("/scorecards/{scorecard_id}/phrases/forbidden")
def get_forbidden_phrases(
    scorecard_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera listę fraz zakazanych dla danej karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    # Jeśli to domyślna karta SERVICE, zwróć z kodu
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        default_config = get_default_service_scorecard()
        return {"phrases": default_config.get("forbidden_phrases", [])}
    
    return {"phrases": scorecard.forbidden_phrases or []}

@router.put("/scorecards/{scorecard_id}/phrases/required")
def update_required_phrases(
    scorecard_id: int,
    phrase_update: PhraseUpdate,
    db: Session = Depends(get_db)
):
    """
    Aktualizuje listę fraz obowiązkowych dla danej karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    # Nie można modyfikować domyślnej karty (id=0 lub SERVICE_DEFAULT)
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    scorecard.required_phrases = phrase_update.phrases
    db.commit()
    db.refresh(scorecard)
    
    return {"message": "Frazy obowiązkowe zaktualizowane", "phrases": scorecard.required_phrases}

@router.put("/scorecards/{scorecard_id}/phrases/forbidden")
def update_forbidden_phrases(
    scorecard_id: int,
    phrase_update: PhraseUpdate,
    db: Session = Depends(get_db)
):
    """
    Aktualizuje listę fraz zakazanych dla danej karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    # Nie można modyfikować domyślnej karty (id=0 lub SERVICE_DEFAULT)
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    scorecard.forbidden_phrases = phrase_update.phrases
    db.commit()
    db.refresh(scorecard)
    
    return {"message": "Frazy zakazane zaktualizowane", "phrases": scorecard.forbidden_phrases}

class PhraseAdd(BaseModel):
    """Model do dodawania pojedynczej frazy"""
    phrase: str

@router.post("/scorecards/{scorecard_id}/phrases/required")
def add_required_phrase(
    scorecard_id: int,
    phrase_data: PhraseAdd,
    db: Session = Depends(get_db)
):
    """
    Dodaje pojedynczą frazę obowiązkową do karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    phrases = scorecard.required_phrases or []
    if phrase_data.phrase not in phrases:
        phrases.append(phrase_data.phrase)
        scorecard.required_phrases = phrases
        db.commit()
        db.refresh(scorecard)
    
    return {"message": "Fraza dodana", "phrases": scorecard.required_phrases}

@router.post("/scorecards/{scorecard_id}/phrases/forbidden")
def add_forbidden_phrase(
    scorecard_id: int,
    phrase_data: PhraseAdd,
    db: Session = Depends(get_db)
):
    """
    Dodaje pojedynczą frazę zakazaną do karty oceny.
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    phrases = scorecard.forbidden_phrases or []
    if phrase_data.phrase not in phrases:
        phrases.append(phrase_data.phrase)
        scorecard.forbidden_phrases = phrases
        db.commit()
        db.refresh(scorecard)
    
    return {"message": "Fraza dodana", "phrases": scorecard.forbidden_phrases}

@router.delete("/scorecards/{scorecard_id}/phrases/required")
def delete_required_phrase(
    scorecard_id: int,
    phrase: str = Query(..., description="Fraza do usunięcia"),
    db: Session = Depends(get_db)
):
    """
    Usuwa frazę obowiązkową z karty oceny.
    Użyj parametru query: ?phrase=tekst_frazy
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    phrases = scorecard.required_phrases or []
    if phrase in phrases:
        phrases.remove(phrase)
        scorecard.required_phrases = phrases
        db.commit()
        db.refresh(scorecard)
    
    return {"message": "Fraza usunięta", "phrases": scorecard.required_phrases}

@router.delete("/scorecards/{scorecard_id}/phrases/forbidden")
def delete_forbidden_phrase(
    scorecard_id: int,
    phrase: str = Query(..., description="Fraza do usunięcia"),
    db: Session = Depends(get_db)
):
    """
    Usuwa frazę zakazaną z karty oceny.
    Użyj parametru query: ?phrase=tekst_frazy
    """
    scorecard = db.query(ScorecardConfig).filter(
        ScorecardConfig.id == scorecard_id
    ).first()
    
    if not scorecard:
        raise HTTPException(status_code=404, detail="Karta oceny nie znaleziona")
    
    if scorecard_id == 0 or scorecard.name == "SERVICE_DEFAULT":
        raise HTTPException(
            status_code=400,
            detail="Nie można modyfikować domyślnej karty. Utwórz własną kartę."
        )
    
    phrases = scorecard.forbidden_phrases or []
    if phrase in phrases:
        phrases.remove(phrase)
        scorecard.forbidden_phrases = phrases
        db.commit()
        db.refresh(scorecard)
    
    return {"message": "Fraza usunięta", "phrases": scorecard.forbidden_phrases}

