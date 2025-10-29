from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .api.endpoints import audio, transcription, diarization, evaluation, scorecard
from .database import Base, engine

# Tworzymy tabele w bazie danych
Base.metadata.create_all(bind=engine)

app = FastAPI(title="System Oceny Rozmów (SOR)")

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji należy zmienić na konkretne domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfiguracja static files i templates
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

# Dodatkowe mounty dla backward compatibility (jeśli przeglądarka cache'uje)
app.mount("/css", StaticFiles(directory=str(BASE_DIR / "app" / "static" / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(BASE_DIR / "app" / "static" / "js")), name="js")

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# Główna strona aplikacji (MUSI być PRZED routerami API)
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def root(request: Request):
    """Główna strona aplikacji - ZAWSZE zwraca HTML"""
    html_file = BASE_DIR / "app" / "templates" / "index.html"
    
    if not html_file.exists():
        return HTMLResponse(content=f"""
        <html><body>
        <h1>Błąd: Plik nie istnieje!</h1>
        <p>Ścieżka: {html_file}</p>
        <p>BASE_DIR: {BASE_DIR}</p>
        </body></html>
        """)
    
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content, media_type="text/html")

# Dodajemy routery API
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(transcription.router, prefix="/api/transcription", tags=["transcription"])
app.include_router(diarization.router, prefix="/api/diarization", tags=["diarization"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(scorecard.router, prefix="/api", tags=["scorecard"])