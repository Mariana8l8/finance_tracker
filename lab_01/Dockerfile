FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FINANCE_TRACKER_APP_NAME="Finance Tracker API"
ENV APP_ENV=production
ENV DATABASE_URL=sqlite:////app/data/finance_tracker.db
ENV LOG_LEVEL=INFO

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

RUN mkdir -p /app/data \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "finance_tracker.api:app", "--host", "0.0.0.0", "--port", "8000"]
