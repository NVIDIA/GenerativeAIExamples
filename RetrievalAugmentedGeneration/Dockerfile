ARG BASE_IMAGE_URL=nvcr.io/nvidia/pytorch
ARG BASE_IMAGE_TAG=23.08-py3


FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}
COPY chain_server /opt/chain_server
RUN --mount=type=bind,source=requirements.txt,target=/opt/requirements.txt \
    python3 -m pip install --no-cache-dir -r /opt/requirements.txt

WORKDIR /opt
ENTRYPOINT ["uvicorn", "chain_server.server:app"]
