# Użyj oficjalnego obrazu Pythona
FROM python:3.11-slim

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj plik zależności
COPY requirements.txt .

# Zainstaluj zależności
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj całą aplikację
COPY . .

# Ustaw zmienne środowiskowe
ENV PYTHONUNBUFFERED=1

# Port dla aplikacji
EXPOSE 8000

# Uruchom aplikację
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

