FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Даем права пользователю appuser (если он есть)
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app



ENV GDAL_VERSION=3.6.0

USER appuser

EXPOSE 8080

CMD ["python", "app.py"]