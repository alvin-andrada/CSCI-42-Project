FROM python:3.11

ENV PYTHONBUFFERED 1

RUN apt-get update && apt-get install -y \
    postgresql-client postgresql-client-common gettext

WORKDIR /app

COPY . /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 80


