#!/bin/sh
set -e
exec /opt/venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers ${WORKERS:-$(( $(nproc) * 2 + 1 ))} \
    --worker-connections ${WORKER_CONNECTIONS:-1000} \
    --timeout ${TIMEOUT:-60} \
    --keep-alive ${KEEP_ALIVE:-5} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --worker-tmp-dir /dev/shm \
    --preload