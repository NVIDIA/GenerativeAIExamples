helm:
	../hack/helmer.sh

GRAPH ?= ${HOME}/github.com/zvonkok/helmer/graphs/helmer-nfd.yaml

run: helm
	go mod tidy
	go mod vendor
	cp patches/root.go vendor/helm.sh/helm/v3/pkg/chart/.
	go run . -g $(GRAPH)


