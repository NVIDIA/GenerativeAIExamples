#!/bin/bash

HELM_PLUGINS=$(realpath ../plugins)
export HELM_PLUGINS 

HELM_CHARTS_DIR=${HOME}/helm-charts
HELM_REPOS=$(ls -d ${HELM_CHARTS_DIR}/*)
HELM_TMP_DIR=$(mktemp -d)

function lint {
        helm lint --with-subcharts --strict "${CHARTS}"
}

function package {
        helm package "${CHARTS}" --destination "${REPO}"
}

function repo_index {
        helm repo index "${REPO}" --url=file:///${REPO}
}

function dependency_update {
        for CHART in ${CHARTS}
        do
                helm dependency update "${CHART}"
        done
}

function template {
        for CHART in ${CHARTS}
        do
                MANIFESTS=${HELM_TMP_DIR}/$(basename "${CHART}").yaml
                echo "==> Templating ${CHART}"
                echo "[INFO] ${MANIFESTS}"
                echo ""
                helm template --name-template=nvidia "${CHART}" > "${MANIFESTS}"
        done
}


function kube_linter {
        echo "kube-linter"
}

function helmer_prereq {
        ln -sf "${HELM_PLUGINS}" /tmp/.helmplugins
}

function helmer {
        COMMAND=$1
        for REPO in ${HELM_REPOS}
        do
                CHARTS=$(ls -d "${REPO}"/*/)
                ${COMMAND}
        done
}


helmer_prereq

#helmer lint
helmer dependency_update
helmer package
helmer repo_index
helmer lint
helmer template
helmer kube_linter

