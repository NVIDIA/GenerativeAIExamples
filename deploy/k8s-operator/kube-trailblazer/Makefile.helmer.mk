

.PHONY: go-mod
go-mod: ## Runs go mod tidy/vendor to sync vendor directory with go.mod.
	go mod tidy
	go mod vendor

.PHONY: patch
patch:
	cp .patches/root.go vendor/helm.sh/helm/v3/pkg/chart/.

