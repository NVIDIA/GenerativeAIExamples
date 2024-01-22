FROM docker.io/library/python:3.11-slim

RUN mkdir /app
COPY requirements.txt /app
RUN apt-get update; \
    apt-get upgrade -y; \
    python3 -m pip --no-cache-dir install -r /app/requirements.txt; \
    python3 -m pip --no-cache-dir install nvidia-riva-client==2.14.0; \
    apt-get clean
USER 1001
COPY frontend /app/frontend

WORKDIR /app
ENTRYPOINT ["python3", "-m", "frontend"]
