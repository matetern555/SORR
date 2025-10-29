from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from ...database import get_db
from ...models.audio import AudioFile
from ...schemas.audio import AudioFile as AudioFileSchema, AudioFileCreate

router = APIRouter()

AUDIO_UPLOAD_DIR = "uploads/audio"
ALLOWED_EXTENSIONS = {"mp3", "wav"}

# Upewnij się, że katalog istnieje
os.makedirs(AUDIO_UPLOAD_DIR, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS

@router.post("/upload/", response_model=AudioFileSchema)
async def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Dozwolone tylko pliki MP3 i WAV"
        )
    
    # Generuj unikalną nazwę pliku
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(AUDIO_UPLOAD_DIR, filename)
    
    # Zapisz plik
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas zapisywania pliku: {str(e)}"
        )
    
    # Zapisz informacje w bazie danych
    db_audio = AudioFile(
        filename=filename,
        file_path=file_path,
        file_type=file.filename.split(".")[-1].lower(),
        duration=0.0  # TODO: Dodać rzeczywiste obliczanie długości
    )
    
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    
    return db_audio

@router.get("/files/", response_model=List[AudioFileSchema])
def list_audio_files(db: Session = Depends(get_db)):
    return db.query(AudioFile).all()

@router.get("/files/{file_id}", response_model=AudioFileSchema)
def get_audio_file(file_id: int, db: Session = Depends(get_db)):
    db_audio = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if db_audio is None:
        raise HTTPException(status_code=404, detail="Plik nie znaleziony")
    return db_audio




