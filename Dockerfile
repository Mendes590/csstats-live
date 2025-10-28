# Força arquitetura amd64 no build do Render (evita tentar compilar greenlet em arm64)
ARG TARGETPLATFORM
FROM --platform=linux/amd64 mcr.microsoft.com/playwright/python:v1.45.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PIP_ONLY_BINARY=:all: \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NODE_OPTIONS=--max-old-space-size=128

WORKDIR /app

COPY requirements.txt ./

# 1) pip moderno + wheels binários
# 2) instala direto o greenlet via wheel (se disponível)
# 3) instala demais deps
# 4) baixa os browsers do Playwright
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --only-binary=:all: greenlet==3.0.3 && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps

COPY . .

EXPOSE 8000

# Render injeta $PORT. Use 1 worker para não abrir 2 browsers no plano básico.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
