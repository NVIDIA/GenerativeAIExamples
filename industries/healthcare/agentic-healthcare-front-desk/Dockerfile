ARG BASE_IMAGE_URL=nvcr.io/nvidia/base/ubuntu
ARG BASE_IMAGE_TAG=22.04_20240212

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

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


# install dependencies
RUN apt update &&  apt-get install -y python3-dev build-essential 
RUN pip install --upgrade pip && pip install --upgrade setuptools
COPY ./requirements.txt /opt/requirements.txt 
RUN  pip3 install --no-cache-dir --use-pep517 -r /opt/requirements.txt


COPY ./ /app

WORKDIR /app

#ENTRYPOINT ["python", "chain_server.py"]

