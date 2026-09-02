FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.model_cache

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY crawler/requirements.txt /app/requirements.txt

# torch'un CPU-only tekerleği: imaj ~2.5GB yerine ~900MB kalıyor.
RUN pip install --no-cache-dir \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      -r /app/requirements.txt

COPY crawler/ /app/
COPY db/ /app/db/

ENV PYTHONPATH=/app

CMD ["python", "-m", "run_all"]
