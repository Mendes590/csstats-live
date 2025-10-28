# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Importante: 1 worker e limite de conexões simultâneas
ENV WEB_CONCURRENCY=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "1", "--timeout-keep-alive", "5"]
