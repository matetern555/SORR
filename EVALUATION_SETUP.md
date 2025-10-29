# 🎯 Instrukcja konfiguracji oceny rozmów

## ✅ Co zostało zaimplementowane

1. **Model bazy danych** (`app/models/evaluation.py`):
   - Tabela `evaluations` - główna ocena rozmowy
   - Tabela `category_scores` - oceny po kategoriach
   - Tabela `quotes` - cytaty (dowody) z kategorii

2. **Schematy Pydantic** (`app/schemas/evaluation.py`):
   - `EvaluationResult` - pełny wynik oceny
   - `CategoryScore` - ocena kategorii
   - `Quote` - cytat

3. **Serwis oceny** (`app/services/evaluation.py`):
   - Integracja z GPT-4
   - 6 kategorii SERVICE zgodnie ze specyfikacją
   - System prompt zgodny ze specyfikacją
   - Obliczanie wyników i ocen literowych

4. **Endpointy API** (`app/api/endpoints/evaluation.py`):
   - `POST /api/evaluation/evaluate/{transcription_id}` - ocena rozmowy
   - `GET /api/evaluation/evaluations/{transcription_id}` - pobierz ocenę
   - `GET /api/evaluation/evaluations/` - lista wszystkich ocen

## ⚙️ Konfiguracja

### 1. Dodaj klucz API OpenAI

Otwórz plik `app/services/evaluation.py` i znajdź funkcję `get_openai_client()`:

```python
def get_openai_client():
    """Tworzy i zwraca klienta OpenAI"""
    # TODO: Usunąć hardkod po naprawie pliku .env
    api_key = os.getenv("OPENAI_API_KEY") or "sk-proj-..."
    
    if not api_key or api_key == "sk-proj-...":
        raise ValueError("Brak klucza API OpenAI. Sprawdź plik .env lub dodaj klucz bezpośrednio w kodzie")
    
    return OpenAI(api_key=api_key)
```

**Zamień** `"sk-proj-..."` na **Twój prawdziwy klucz API OpenAI**.

### 2. Zainstaluj wymagane biblioteki

```bash
.\venv\Scripts\pip.exe install openai
```

### 3. Zrestartuj serwer

```bash
# Zatrzymaj serwer (Ctrl+C) i uruchom ponownie:
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testowanie

### Sprawdź dostępne endpointy

```bash
.\venv\Scripts\python.exe -c "import requests; api = requests.get('http://localhost:8000/openapi.json').json(); paths = [p for p in api['paths'].keys() if 'evaluation' in p]; print('Endpoints:'); [print('  -', p) for p in paths]"
```

Powinieneś zobaczyć:
```
Endpoints:
  - /api/evaluation/evaluate/{transcription_id}
  - /api/evaluation/evaluations/{transcription_id}
  - /api/evaluation/evaluations/
```

### Oceń rozmowę

```bash
.\venv\Scripts\python.exe -c "import requests; response = requests.post('http://localhost:8000/api/evaluation/evaluate/1?scorecard_type=SERVICE'); print('Status:', response.status_code); print('Response:', response.json())"
```

## 📊 Kategorie oceny (SERVICE)

1. **Powitanie i ton** (10%) - pierwsze wrażenie
2. **Identyfikacja problemu** (20%) - trafne pytania i potwierdzenie
3. **Rozwiązanie sprawy** (25%) - skuteczność i jasność pomocy
4. **Jasność komunikacji** (15%) - prosty język, tempo
5. **Finalizacja rozmowy** (15%) - domknięcie i pozytywne zakończenie
6. **Soft-skills** (15%) - empatia, cierpliwość

## 📈 Skala ocen

- **A** - 85-100% - Wzorowo
- **B** - 75-84% - Dobrze
- **C** - 60-74% - Poprawnie
- **D** - <60% - Wymaga poprawy

## 🎓 Co zwraca GPT-4

Dla każdej kategorii:
- Ocena 1-5
- Krótki komentarz
- 1-2 cytaty z czasem

Dodatkowo:
- Sentyment klienta (start, end, delta, cytat)
- Sentyment konsultanta (start, end, delta, cytat)
- Komentarz końcowy (2-4 zdania)

## 🔧 Rozwiązywanie problemów

### Błąd: "Brak klucza API OpenAI"
- Sprawdź czy klucz został dodany w `app/services/evaluation.py`
- Upewnij się że klucz jest poprawny

### Błąd: "Brak segmentów mówców"
- Najpierw wykonaj diaryzację: `POST /api/diarization/analyze/{transcription_id}`
- Dopiero potem ocenę

### Błąd: "Transkrypcja nie znaleziona"
- Sprawdź czy transkrypcja o podanym ID istnieje
- Najpierw prześlij audio i wykonaj transkrypcję

## 📝 Następne kroki

Po poprawnym skonfigurowaniu możesz:
1. Przetestować ocenę na przykładowej rozmowie
2. Sprawdzić wynik w bazie danych
3. Wygenerować raporty i dashboard
4. Dodać pozostałe karty oceny (SALES, RETENTION, COLLECTIONS)

