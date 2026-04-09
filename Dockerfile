FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PAPER_ASSISTANT_HOST=0.0.0.0 \
    PAPER_ASSISTANT_PORT=8000

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY scripts ./scripts
COPY tests ./tests
COPY main.py README.md ./

RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "backend.app.presentation.wsgi:app", "--workers", "1", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:8000"]

