FROM python:3.11

ENV PYTHONBUFFERED 1

WORKDIR /app

COPY . /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 80


