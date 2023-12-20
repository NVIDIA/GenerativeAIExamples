HELM_CHARTS_DIR = helm-charts
HELM_BUILD_ROOT_DIR = build
HELM_BUILD_DIR = $(HELM_BUILD_ROOT_DIR)/$(HELM_CHARTS_DIR)
HELM_REPOS = $(shell ls -d $(HELM_BUILD_DIR)/*/)



helm-lint: helm helm-copy-charts
	@echo "=> HelmRepo: $(HELM_REPOS)"
	@for repo in $(HELM_REPOS); do \
		cd $$repo; \
		helm lint -f ../global-values.yaml `ls -d */`; \
		cd ../../..; \
	done

helm-repo-index: helm-lint
	@for repo in $(HELM_REPOS); do \
		cd $$repo; \
		helm package `ls -d */`; \
		file_url=`echo $$repo |sed 's/$(HELM_BUILD_ROOT_DIR)\///g'`; \
		helm repo index . --url=file:///$$file_url; \
		cd ../../..; \
	done


helm-copy-charts:
	rm -rf $(HELM_BUILD_DIR)
	mkdir -p $(HELM_BUILD_DIR)
	cp -r $(HELM_CHARTS_DIR)/* $(HELM_BUILD_DIR)


helm:
ifeq (, $(shell which helm))
	@{ \
	set -e ;\
	HELM_GEN_TMP_DIR=$$(mktemp -d) ;\
	cd $$HELM_GEN_TMP_DIR ;\
	OS=$(shell go env GOOS) && ARCH=$(shell go env GOARCH); \
	curl https://get.helm.sh/helm-v3.6.0-$$OS-$$ARCH.tar.gz -o helm.tar.gz ;\
	tar xvfpz helm.tar.gz ;\
	mv linux-amd64/helm /usr/local/bin ;\
	chmod +x /usr/local/bin/helm ;\
	rm -rf $$HELM_GEN_TMP_DIR ;\
	}
HELM=/usr/local/bin/helm
else
HELM=$(shell which helm)
endif


# Operator specific

CSPLIT ?= csplit - --prefix="" --suppress-matched --suffix-format="%04d_operator_manifests.yaml"  /---/ '{*}' 1>/dev/null
HELM_CHART_NAME = developer-llm-operator

.PHONY: helm-chart

helm-chart: manifests kustomize ## Deploy controller to the K8s cluster specified in ~/.kube/config.
	cd config/manager && $(KUSTOMIZE) edit set image controller=${IMG}
	cd $(HELM_CHARTS_DIR)/staging/$(HELM_CHART_NAME)/templates && $(KUSTOMIZE) build ../../../../config/default | $(CSPLIT)
## Remove namespace creation, helm can do that ...
	rm $(HELM_CHARTS_DIR)/staging/$(HELM_CHART_NAME)/templates/0000_operator_manifests.yaml
