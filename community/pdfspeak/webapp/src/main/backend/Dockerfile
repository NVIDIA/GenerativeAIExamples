FROM python:3.13-slim
WORKDIR /usr/src/app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire nv-ingest directory
COPY nv-ingest /usr/src/app/nv-ingest

# Install nv-ingest client
RUN pip install -e /usr/src/app/nv-ingest/client
RUN pip install --no-cache-dir -r /usr/src/app/nv-ingest/client/requirements.txt

# Copy and install main requirements
COPY webapp/src/main/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY webapp/src/main/backend .
#COPY webapp/src/main/backend/.certs /usr/src/app/.certs
COPY webapp/src/main/backend/audio_outputs /usr/src/app/audio_outputs
COPY webapp/src/main/backend/uploads /usr/src/app/uploads

EXPOSE 5050
CMD ["python", "-m", "marshaler.chat_io_service"]
