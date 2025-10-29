# Plan Wdrożenia Systemu Oceny Rozmów (SOR)

## Założenia ogólne
1. Zaczynamy od najprostszych funkcjonalności
2. Każdy etap daje działający produkt
3. Używamy gotowych rozwiązań gdzie to możliwe
4. System jest testowalny na każdym etapie
5. Funkcjonalności dodawane są przyrostowo

## Etapy wdrożenia

### 1. Przygotowanie środowiska projektu
- **Technologie:**
  - Backend: Python (Flask/FastAPI)
  - Frontend: React
  - Baza danych: PostgreSQL
- **Podstawowa struktura:**
  - Konfiguracja projektu
  - System autoryzacji
  - Prosty interfejs do wgrywania plików

### 2. Obsługa plików audio
- Implementacja uploadu plików MP3/WAV przez przeglądarkę
- Walidacja plików audio
- System przechowywania nagrań
- Podstawowe zarządzanie plikami (lista, usuwanie)

### 3. Transkrypcja audio
- Integracja z API transkrypcji (OpenAI Whisper)
- System wyświetlania transkrypcji
- Implementacja timestampów
- Podstawowa edycja transkrypcji

### 4. Diaryzacja
- Integracja z systemem rozpoznawania mówców
- Połączenie z systemem transkrypcji
- Oznaczenia KLIENT/KONSULTANT
- Interfejs do weryfikacji/korekty oznaczeń

### 5. System kart oceny (Scorecards)
- Implementacja podstawowego systemu scorecardów
- Predefiniowane karty (SALES, SERVICE, RETENTION, COLLECTIONS)
- Interfejs oceny rozmów
- System wag i punktacji

### 6. Analiza sentymentu
- System analizy emocji w rozmowie
- Wykresy zmian sentymentu
- Integracja z systemem ocen
- Wizualizacja trendów emocjonalnych

### 7. System raportowania
- Generator raportów podstawowych
- Eksport do PDF/XLS
- Dashboard statystyk
- System filtrów i wyszukiwania

### 8. Integracja z PBX/VoIP
- Integracja z pierwszym systemem telefonicznym
- System harmonogramów
- Automatyczne pobieranie rozmów
- Konfiguracja reguł importu

## Szczegóły techniczne

### Stack technologiczny
- **Backend:**
  - Python 3.11+
  - FastAPI/Flask
  - PostgreSQL
  - Redis (cache)

- **Frontend:**
  - React 18+
  - TypeScript
  - Material-UI/Tailwind
  - React Query

- **Infrastruktura:**
  - Docker
  - Docker Compose
  - Nginx
  - Let's Encrypt (SSL)

### Wymagania systemowe
- Linux/Windows Server
- Min. 16GB RAM
- Min. 4 rdzenie CPU
- SSD dla bazy danych
- Przestrzeń dyskowa zależna od liczby nagrań

### Bezpieczeństwo
- Szyfrowanie danych w spoczynku
- HTTPS
- Uwierzytelnianie JWT
- Role i uprawnienia
- Audyt działań użytkowników

## Kolejne kroki
1. Utworzenie repozytorium
2. Konfiguracja środowiska deweloperskiego
3. Implementacja pierwszej funkcjonalności
4. Testy i iteracyjne ulepszenia

## Uwagi
- Każdy etap kończy się działającym produktem
- Możliwość testowania na rzeczywistych danych
- Elastyczność w dostosowaniu do potrzeb
- Skalowalność rozwiązania





