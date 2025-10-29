# 🚀 Instrukcja wdrożenia na Render.com

## 📋 Wymagania

- Konto na [Render.com](https://render.com) (darmowe)
- Repozytorium Git (GitHub, GitLab lub Bitbucket)
- Klucze API: OpenAI i Deepgram

## 🎯 Plan wdrożenia

### **Render.com** - zalecane rozwiązanie
- ✅ Darmowy plan PostgreSQL
- ✅ Darmowy plan Web Service (z ograniczeniami)
- ✅ Automatyczne deploy z Git
- ✅ HTTPS out of the box
- ⚠️ Web Service przechodzi w stan "sleep" po 15 minutach bezczynności (darmowy plan)

### **Alternatywne opcje** (jeśli Render nie wystarczy):

1. **Railway.app** - $5 kredyt miesięcznie za darmo
   - Lepsze dla aplikacji z długimi requestami
   - Szybsze "wake up" po sleep

2. **Fly.io** - Darmowy plan z ograniczeniami
   - Trudniejsza konfiguracja
   - Wymaga CLI

## 📝 Krok po kroku - Render.com

### 1. Przygotuj repozytorium Git

```bash
# Jeśli jeszcze nie masz repozytorium Git:
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Dodaj remote (GitHub/GitLab/Bitbucket):
git remote add origin https://github.com/TWOJ_USERNAME/SORR.git
git push -u origin main
```

### 2. Utwórz bazę danych PostgreSQL na Render

1. Zaloguj się na [Render.com](https://render.com)
2. Kliknij **"New +"** → **"PostgreSQL"**
3. Konfiguracja:
   - **Name**: `sor-db`
   - **Database**: `sor`
   - **User**: `sor_user`
   - **Region**: wybierz najbliższy (np. Frankfurt)
   - **Plan**: **Free**
4. Kliknij **"Create Database"**
5. **Zapisz** wyświetlony **"Internal Database URL"** (będzie potrzebny później)

### 3. Utwórz Web Service

1. W panelu Render kliknij **"New +"** → **"Web Service"**
2. Podłącz swoje repozytorium Git:
   - Wybierz provider (GitHub/GitLab/Bitbucket)
   - Wybierz repozytorium `SORR`
   - Kliknij **"Connect"**
3. Konfiguracja:
   - **Name**: `sor-app`
   - **Region**: ten sam co baza danych
   - **Branch**: `main`
   - **Root Directory**: zostaw puste
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**
4. Kliknij **"Advanced"** i dodaj zmienne środowiskowe:

   ```
   DATABASE_URL=<Internal Database URL z kroku 2>
   OPENAI_API_KEY=<Twój klucz OpenAI>
   DEEPGRAM_API_KEY=<Twój klucz Deepgram>
   PYTHON_VERSION=3.11.0
   ```

5. Kliknij **"Create Web Service"**

### 4. Czekaj na deploy

- Render automatycznie zbuduje i uruchomi aplikację
- Możesz obserwować logi w czasie rzeczywistym
- Po zakończeniu dostaniesz URL: `https://sor-app.onrender.com`

### 5. Weryfikacja

1. Otwórz URL aplikacji w przeglądarce
2. Sprawdź czy strona się ładuje
3. Przetestuj upload pliku audio i analizę

## ⚙️ Alternatywa: użycie render.yaml (automatyczna konfiguracja)

Jeśli plik `render.yaml` jest w repozytorium:

1. Render automatycznie wykryje plik
2. Zostaniesz poproszony o podłączenie repo z plikiem `render.yaml`
3. Render utworzy wszystkie serwisy automatycznie
4. Musisz tylko dodać zmienne środowiskowe (`OPENAI_API_KEY`, `DEEPGRAM_API_KEY`)

## ⚠️ Ograniczenia darmowego planu Render

- **Sleep mode**: Po 15 minutach bezczynności aplikacja przechodzi w stan "sleep"
- **Cold start**: Pierwsze żądanie po sleep może zająć 30-60 sekund
- **Ograniczenia**: 750 godzin/miesiąc (wystarczy dla testów)

## 🔧 Rozwiązywanie problemów

### Błąd: "Database connection failed"
- Sprawdź czy `DATABASE_URL` jest poprawnie ustawione
- Upewnij się że używasz **Internal Database URL** (nie publicznego)

### Błąd: "Module not found"
- Sprawdź `requirements.txt` czy wszystkie zależności są tam
- Upewnij się że `buildCommand` instaluje zależności

### Aplikacja nie odpowiada
- Sprawdź logi w panelu Render
- Upewnij się że port jest ustawiony na `$PORT` (Render automatycznie go ustawia)

### Baza danych nie ma tabel
- Render automatycznie uruchomi `Base.metadata.create_all()` przy starcie
- Jeśli nie, możesz dodać migrację Alembic (opcjonalnie)

## 📚 Przydatne linki

- [Render.com Dashboard](https://dashboard.render.com)
- [Render.com Docs](https://render.com/docs)
- [Darmowy plan Render](https://render.com/docs/free)

## 🎉 Gotowe!

Po wdrożeniu aplikacja będzie dostępna pod adresem:
`https://sor-app.onrender.com`

Możesz podzielić się tym linkiem z innymi użytkownikami!

