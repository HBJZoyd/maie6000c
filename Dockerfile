FROM python:3.11-slim@sha256:b7a9e5f6a93d6d4a31f129bbd4bdee69efccb6ded0fb230d78aafaf37af98377 AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.app.lock /app/

# Keep dependency installation cached when only application code changes.
RUN pip install --upgrade 'pip==26.3' 'setuptools==84.2.1' 'wheel==0.48.0' && \
    pip install -r requirements.app.lock

COPY pyproject.toml README.md /app/

COPY services /app/services
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

RUN pip install --no-deps --no-build-isolation -e .

CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS tests
COPY requirements.test.lock /app/
RUN pip install -r requirements.test.lock
COPY tests /app/tests
COPY RAG/src/utils.py /app/RAG/src/utils.py
COPY compose.yaml compose.offline.yaml compose.test.yaml /app/

FROM runtime AS application
