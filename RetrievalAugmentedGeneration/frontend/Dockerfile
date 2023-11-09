FROM docker.io/library/python:3.11-slim

COPY frontend /app/frontend
COPY requirements.txt /app
RUN apt-get update; \
    apt-get upgrade -y; \
    python3 -m pip --no-cache-dir install -r /app/requirements.txt; \
    apt-get clean
USER 1001

WORKDIR /app
ENTRYPOINT ["python3", "-m", "frontend"]
