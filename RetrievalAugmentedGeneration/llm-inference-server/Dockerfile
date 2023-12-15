ARG BASE_IMAGE_URL=nvcr.io/nvidia/nemo/nemofw-inference
ARG BASE_IMAGE_TAG=23.10-for-rag

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ENV LD_LIBRARY_PATH=/opt/tritonserver/backends/tensorrtllm:$LD_LIBRARY_PATH

# install model-server automation
COPY conversion_scripts /opt/conversion_scripts
COPY ensemble_models /opt/ensemble_models
COPY model_server /opt/model_server
COPY model_server_client /opt/model_server_client
RUN --mount=type=bind,source=requirements.txt,target=/opt/requirements.txt \
    pip install --no-cache-dir -r /opt/requirements.txt

# Create basic directories

RUN mkdir /model && chmod 1777 /model && \
    mkdir -p /home/triton-server && chown 1000:1000 /home/triton-server && chmod 700 /home/triton-server

WORKDIR /opt
ENTRYPOINT ["/usr/bin/python3", "-m", "model_server"]
