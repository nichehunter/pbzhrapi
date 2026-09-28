# syntax=docker/dockerfile:1
FROM python:3.10-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /hrms

# Install system dependencies including GIS and build requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libgdal-dev \
    gdal-bin \
    postgis \
    postgresql-client \
    sqlite3 \
    spatialite-bin \
    libsqlite3-mod-spatialite \
    gettext \
    cron \
    netcat-openbsd \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Replace the build tools upgrade line with:
RUN pip install --no-cache-dir --upgrade "pip<24.1" "setuptools<70.0.0" wheel

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --timeout 6000 --retries 5

# Copy application files
COPY ./hrms /hrms

EXPOSE 5051