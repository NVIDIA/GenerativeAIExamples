FROM python:3.12

RUN apt-get update
RUN apt-get install -y poppler-utils

WORKDIR /app

COPY ./ingest/requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN pip install -e nv-mm-retrieval-app/packages/nv-mm-ingest-docs
RUN pip install -e nv-mm-retrieval-app/packages/nv-mm-document-qa
RUN pip install -e nv-mm-retrieval-app/packages/nv-mm-images

ENTRYPOINT cd nv-mm-retrieval-app && uvicorn app.server:app --host 0.0.0.0 --port 8000




