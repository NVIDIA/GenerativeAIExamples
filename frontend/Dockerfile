ARG BASE_IMAGE_URL=nvcr.io/nvidia/base/ubuntu
ARG BASE_IMAGE_TAG=22.04_20240212

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND noninteractive

# Install required ubuntu packages for setting up python 3.10
RUN apt update && \
    apt install -y openssl libgl1 linux-libc-dev libksba8 curl software-properties-common build-essential libssl-dev libffi-dev && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && apt install -y python3.10 python3.10-dev python3.10-distutils

# Install pip for python3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

RUN rm -rf /var/lib/apt/lists/*

# Download the sources of apt packages within the container for standard legal compliance
RUN sed -i 's/# deb-src/deb-src/g' /etc/apt/sources.list
RUN apt update
# xz-utils is needed to pull the source and unpack them correctly
RUN apt install xz-utils -y
RUN mkdir -p /legal/source
WORKDIR /legal/source
# Read installed packages, strip all but the package names, pipe to 'apt source' to download respective packages
RUN apt list --installed |  grep -i installed | sed 's|\(.*\)/.*|\1|' | xargs apt source --download-only
# The source is saved in directories as well as tarballs in the current dir
RUN rm xz-utils*
COPY LICENSE-3rd-party.txt /legal/

# Install all custom python dependencies
RUN mkdir /app
COPY ./frontend/requirements.txt /app
RUN apt-get update; \
    apt-get upgrade -y; \
    pip3 --no-cache-dir install -r /app/requirements.txt;

# Uninstall build packages
RUN apt autoremove -y openssl libgl1 linux-libc-dev libksba8 curl software-properties-common build-essential libssl-dev libffi-dev python3.10-dev python3.10-distutils

RUN apt-get clean

COPY ./frontend /app/frontend

WORKDIR /app
ENTRYPOINT ["python3.10", "-m", "frontend"]
