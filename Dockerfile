FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Даем права пользователю appuser (если он есть)
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["python", "app.py"]