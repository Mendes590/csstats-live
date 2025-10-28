FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NODE_OPTIONS=--max-old-space-size=128

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Se vc não usar imagem base do Playwright, aí sim rodaria:
# RUN playwright install --with-deps

COPY . .

EXPOSE 8000

# MUITO IMPORTANTE: usar $PORT que o Render injeta
# e apenas 1 worker (para não abrir 2+ browsers no plano free)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
