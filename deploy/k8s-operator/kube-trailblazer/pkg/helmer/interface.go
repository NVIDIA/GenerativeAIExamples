package helmer

import (
	helmclient "github.com/mittwald/go-helm-client"
	"helm.sh/helm/v3/pkg/chart"
	"helm.sh/helm/v3/pkg/release"
	"k8s.io/client-go/rest"
)

// Interface a helm hepler Helper
type Interface interface {
	InstallOrUpgradePackage() error
	Upgrade() error
	Lint() error
	Template() error
	AddOrUpdateRepo() error
	GetClientsWithKubeConf(path string, kubeContext string) error
	GetClientsWithRestConf(restConf *rest.Config) error
	GetChart(char *helmclient.ChartSpec) (*chart.Chart, error)
	RunChartTests() (bool, error)
	UninstallRelease(spec *helmclient.ChartSpec) error
	ListDeployedReleases() ([]*release.Release, error)
}
