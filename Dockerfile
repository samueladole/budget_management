FROM python:3.12.11-alpine

# Install build dependencies and runtime dependencies in one RUN for smaller layers
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        cargo \
    && apk add --no-cache \
        libressl \
        libffi \
        bash \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /root/.cache

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Use gunicorn to run the app, binding to all interfaces
CMD ["gunicorn", "budget_management.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
