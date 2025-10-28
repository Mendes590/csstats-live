FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# garante que os browsers estão instalados no container (imagem já vem, mas não custa)
RUN playwright install --with-deps

COPY . .

EXPOSE 8000
# 1 worker pra caber no Free; loop padrão do uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
