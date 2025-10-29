# System Oceny Rozmów (SOR)

System do automatycznej oceny rozmów telefonicznych w call center.

## Wymagania systemowe

- Python 3.11+
- PostgreSQL
- Node.js 18+ (dla frontendu)

## Instalacja

1. Sklonuj repozytorium
2. Utwórz wirtualne środowisko Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Skopiuj plik .env.example do .env i uzupełnij zmienne środowiskowe:
```bash
cp .env.example .env
```

5. Uruchom aplikację:
```bash
uvicorn app.main:app --reload
```

## Struktura projektu

```
sor/
├── app/
│   ├── main.py          # Główny plik aplikacji
│   ├── database.py      # Konfiguracja bazy danych
│   ├── models/          # Modele SQLAlchemy
│   ├── schemas/         # Schematy Pydantic
│   ├── api/             # Endpointy API
│   └── services/        # Logika biznesowa
├── tests/               # Testy
├── requirements.txt     # Zależności Pythona
└── README.md           # Dokumentacja
```

## Testowanie

Aplikacja będzie dostępna pod adresem: http://localhost:8000

API dokumentacja (Swagger UI): http://localhost:8000/docs





