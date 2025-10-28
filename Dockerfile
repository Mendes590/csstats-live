# Use uma base Playwright alinhada à sua lib
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PIP_ONLY_BINARY=:all: \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NODE_OPTIONS=--max-old-space-size=128

WORKDIR /app

COPY requirements.txt ./

# Garante pip/setuptools/wheel atualizados e força greenlet/playwright binários
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps

COPY . .

EXPOSE 8000

# Usar a porta que o Render injeta e APENAS 1 worker (evita 2 browsers no plano free)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
