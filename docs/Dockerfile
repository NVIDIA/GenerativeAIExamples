FROM python:3.12-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install --no-install-recommends -y \
      curl \
      rsync \
      openssh-client \
      wget \
      jq \
      git \
      python3-pip \
      lsb-release \
      gpg

RUN wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install --no-install-recommends -y vault=1.10.11-1 \
 && apt-get autoremove \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=docs,target=/docs pip install -r docs/requirements.txt
RUN --mount=type=bind,source=docs,target=/docs pip install -U --no-deps --no-cache-dir -r docs/swagger-requirements.txt