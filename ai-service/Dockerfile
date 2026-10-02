# ============================================================
# VAYORA AI Service — Dockerfile
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Non-root user
RUN groupadd -r vayora && useradd -r -g vayora vayora

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ownership
RUN chown -R vayora:vayora /app
USER vayora

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
