FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy
WORKDIR /app

# libs Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# browsers + SO deps (ok porque no Docker temos root)
RUN playwright install --with-deps

# código
COPY . .

EXPOSE 8000
# 1 worker (Playwright não se dá bem com múltiplos processos baratos)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0",  "--port", "8000", "--workers", "1"]
