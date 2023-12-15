ARG BASE_IMAGE_URL=nvcr.io/nvidia/pytorch
ARG BASE_IMAGE_TAG=23.08-py3


FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}
COPY RetrievalAugmentedGeneration/__init__.py /opt/RetrievalAugmentedGeneration/
COPY RetrievalAugmentedGeneration/common /opt/RetrievalAugmentedGeneration/common
COPY RetrievalAugmentedGeneration/examples /opt/RetrievalAugmentedGeneration/examples
COPY integrations /opt/integrations
RUN --mount=type=bind,source=RetrievalAugmentedGeneration/requirements.txt,target=/opt/requirements.txt \
    python3 -m pip install --no-cache-dir -r /opt/requirements.txt

WORKDIR /opt
ENTRYPOINT ["uvicorn", "RetrievalAugmentedGeneration.common.server:app"]
