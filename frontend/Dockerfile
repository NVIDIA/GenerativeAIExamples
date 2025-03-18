FROM nvcr.io/nvidia/base/ubuntu:22.04_20240212

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy license information
RUN mkdir -p /legal
COPY LICENSE-3rd-party.txt /legal/

WORKDIR /app

RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs

RUN node -v && npm -v

ARG NEXT_PUBLIC_MODEL_NAME
ARG NEXT_PUBLIC_EMBEDDING_MODEL
ARG NEXT_PUBLIC_RERANKER_MODEL
ARG NEXT_PUBLIC_CHAT_BASE_URL
ARG NEXT_PUBLIC_VDB_BASE_URL

ENV NEXT_PUBLIC_MODEL_NAME=${NEXT_PUBLIC_MODEL_NAME}
ENV NEXT_PUBLIC_EMBEDDING_MODEL=${NEXT_PUBLIC_EMBEDDING_MODEL}
ENV NEXT_PUBLIC_RERANKER_MODEL=${NEXT_PUBLIC_RERANKER_MODEL}
ENV NEXT_PUBLIC_CHAT_BASE_URL=${NEXT_PUBLIC_CHAT_BASE_URL}
ENV NEXT_PUBLIC_VDB_BASE_URL=${NEXT_PUBLIC_VDB_BASE_URL}

COPY . /app

RUN npm install

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]