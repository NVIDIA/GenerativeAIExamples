ARG BASE_IMAGE_URL=nvcr.io/nvidia/pytorch
ARG BASE_IMAGE_TAG=23.08-py3

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ARG EXAMPLE_NAME
COPY RetrievalAugmentedGeneration/__init__.py /opt/RetrievalAugmentedGeneration/
COPY RetrievalAugmentedGeneration/common /opt/RetrievalAugmentedGeneration/common
COPY RetrievalAugmentedGeneration/examples/${EXAMPLE_NAME} /opt/RetrievalAugmentedGeneration/example
COPY integrations /opt/integrations
COPY tools /opt/tools
RUN apt-get update && apt-get install -y libpq-dev
RUN --mount=type=bind,source=RetrievalAugmentedGeneration/requirements.txt,target=/opt/requirements.txt \
    python3 -m pip install --no-cache-dir -r /opt/requirements.txt

RUN if [ -f "/opt/RetrievalAugmentedGeneration/example/requirements.txt" ] ; then \
    python3 -m pip install --no-cache-dir -r /opt/RetrievalAugmentedGeneration/example/requirements.txt ; else \
    echo "Skipping example dependency installation, since requirements.txt was not found" ; \
    fi

WORKDIR /opt
ENTRYPOINT ["uvicorn", "RetrievalAugmentedGeneration.common.server:app"]
