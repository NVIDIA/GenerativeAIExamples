FROM python:3.10-slim

# Set working directory
WORKDIR /opt

RUN apt-get update && apt-get install -y unzip wget git libgl1-mesa-glx libglib2.0-0

RUN mkdir /opt/evaluation
COPY ./requirements.txt /opt/evaluation
COPY ./query_rag_with_gt_questions_and_evaluate.py /opt/evaluation
RUN if [ -f "/opt/evaluation/requirements.txt" ] ; then \
    pip3 install --no-cache-dir -r /opt/evaluation/requirements.txt ; else \
    echo "Skipping dependency installation, since requirements.txt was not found" ; \
    fi
