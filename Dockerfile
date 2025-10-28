# Imagem oficial do Playwright com Python + browsers já instalados
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Procfile é ignorado quando você usa Dockerfile no Koyeb
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
