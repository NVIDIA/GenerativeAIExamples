ARG BASE_IMAGE_URL=nvcr.io/nvidia/base/ubuntu
ARG BASE_IMAGE_TAG=22.04_20240212

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND noninteractive

# Install required ubuntu packages for setting up python 3.10
RUN apt update && \
    apt install -y curl software-properties-common libgl1 libglib2.0-0 && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && apt install -y python3.10 && \
    apt-get clean

# Install pip for python3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

RUN rm -rf /var/lib/apt/lists/*

# Uninstall build packages
RUN apt autoremove -y curl software-properties-common

# Install common dependencies for all examples
RUN --mount=type=bind,source=src/chain_server/requirements.txt,target=/opt/requirements.txt \
    pip3 install --no-cache-dir -r /opt/requirements.txt

# TODO Maybe copy app
ARG APP_PATH
COPY ${APP_PATH} /opt/${APP_PATH}
RUN python3.10 -m nltk.downloader averaged_perceptron_tagger

# Copy required common modules for all examples
# TODO copy only relevant files
COPY src/chain_server /opt/src/chain_server
#COPY src/pandasai /opt/src/pandasai
#COPY tools /opt/tools

RUN mkdir /tmp-data/; mkdir /tmp-data/nltk_data/
RUN chmod 777 -R /tmp-data
RUN chown 1000:1000 -R /tmp-data
ENV NLTK_DATA=/tmp-data/nltk_data/
ENV HF_HOME=/tmp-data

WORKDIR /opt
ENTRYPOINT ["uvicorn", "src.chain_server.server:app"]
