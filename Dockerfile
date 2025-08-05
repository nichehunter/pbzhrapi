# syntax=docker/dockerfile:1
FROM python:3.8.3-buster

RUN mkdir /hrms
WORKDIR /hrms

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list

# RUN apt-get install -y ca-certificates wget

# RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN wget --no-check-certificate --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# This section is borrowed from the official Django image but adds GDAL and others
RUN apt-get update && apt-get install -y \
        libpq-dev python-dev libxml2-dev \
        libxml2 libxslt1-dev zlib1g-dev libjpeg-dev \
        libmemcached-dev libldap2-dev libsasl2-dev libffi-dev


RUN apt-get update && apt-get install -y \
        gcc zip gettext geoip-bin cron netcat \
        postgresql-client-12 \
        postgis postgresql-13-postgis-3 \
        sqlite3 spatialite-bin libsqlite3-mod-spatialite \
        python3-gdal python3-psycopg2 python3-ldap \
        python3-pip python3-pil python3-lxml python3-pylibmc \
        python3-dev libgdal-dev \
        --no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils


RUN pip install --upgrade pip setuptools


RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt --timeout 6000 --retries 5 --verbose
COPY ./hrms /hrms

EXPOSE 5051
