FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/

# Keep dependency installation cached when only application code changes.
RUN pip install --upgrade pip "setuptools>=80.0.0" wheel && \
    python -c "import subprocess, sys, tomllib; subprocess.check_call([sys.executable, '-m', 'pip', 'install', *tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']])"

COPY services /app/services
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

RUN pip install --no-deps --no-build-isolation -e .

CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
