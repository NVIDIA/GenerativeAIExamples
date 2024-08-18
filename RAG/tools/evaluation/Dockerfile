FROM python:3.10-slim

# Set working directory
WORKDIR /opt

RUN apt-get update && apt-get install -y unzip wget git libgl1-mesa-glx libglib2.0-0

ARG DIRECTORY_NAME
COPY RAG/tools/evaluation/${DIRECTORY_NAME}/ /opt/tools/evaluation
RUN if [ -f "/opt/tools/evaluation/requirements.txt" ] ; then \
    pip3 install --no-cache-dir -r /opt/tools/evaluation/requirements.txt ; else \
    echo "Skipping example dependency installation, since requirements.txt was not found" ; \
    fi
