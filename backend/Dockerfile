FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt && \
    rm -rf /root/.cache

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; exec('try: urllib.request.urlopen(\"http://localhost:8000/health\")\nexcept: exit(1)')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
