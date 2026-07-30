FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /app/backend/requirements.txt

COPY backend /app/backend

RUN mkdir -p \
    /app/backend/storage/uploads \
    /app/backend/storage/faiss_index \
    /app/logs

EXPOSE 8000

CMD ["uvicorn","backend.app:app","--host","0.0.0.0","--port","8000"]
