package helmer

import (
	"time"

	helmclient "github.com/mittwald/go-helm-client"
	"github.com/mittwald/go-helm-client/values"
	"github.com/nvidia/kube-trailblazer/pkg/clients"
	"helm.sh/helm/v3/pkg/chartutil"
)

// Type Guard asserting that Helmer satisfies the Helmer interface.
var _ Interface = &Helmer{}

// Helmer describes the resource to be built
type Helmer struct {
	Package    HelmPackage                   `json:"helmArbor"`
	Client     helmclient.Client             `json:"helmClient"`
	Options    helmclient.GenericHelmOptions `json:"helmOptions"`
	KubeClient clients.ClientsInterface      `json:"kubeClient"`
	Debug      bool                          `json:"debug"`
}

// Entry represents a collection of parameters for chart repository, since
// we cannot annotate the internal helm struct we're doing it here
type repoEntry struct {
	// +kubebuilder:validation:Optional
	Name string `json:"name"`
	URL  string `json:"url"`
	// +kubebuilder:validation:Optional
	Username string `json:"username"`
	// +kubebuilder:validation:Optional
	Password string `json:"password"`
	// +kubebuilder:validation:Optional
	CertFile string `json:"certFile"`
	// +kubebuilder:validation:Optional
	KeyFile string `json:"keyFile"`
	// +kubebuilder:validation:Optional
	CAFile string `json:"caFile"`
	// +kubebuilder:validation:Optional
	InsecureSkipTLSverify bool `json:"insecure_skip_tls_verify"`
	// +kubebuilder:validation:Optional
	PassCredentialsAll bool `json:"pass_credentials_all"`
}
type chartSpec struct {
	// +kubebuilder:validation:Optional
	ReleaseName string `json:"release"`
	ChartName   string `json:"chart"`
	// Namespace where the chart release is deployed.
	// Note that helmclient.Options.Namespace should ideally match the namespace configured here.
	// +kubebuilder:validation:Optional
	Namespace string `json:"namespace"`
	// ValuesYaml is the values.yaml content.
	// use string instead of map[string]interface{}
	// https://github.com/kubernetes-sigs/kubebuilder/issues/528#issuecomment-466449483
	// and https://github.com/kubernetes-sigs/controller-tools/pull/317
	// +optional
	ValuesYaml string `json:"valuesYaml,omitempty"`
	// Specify values similar to the cli
	// +optional
	ValuesOptions values.Options `json:"valuesOptions,omitempty"`
	// Version of the chart release.
	// +optional
	Version string `json:"version,omitempty"`
	// CreateNamespace indicates whether to create the namespace if it does not exist.
	// +optional
	CreateNamespace bool `json:"createNamespace,omitempty"`
	// DisableHooks indicates whether to disable hooks.
	// +optional
	DisableHooks bool `json:"disableHooks,omitempty"`
	// Replace indicates whether to replace the chart release if it already exists.
	// +optional
	Replace bool `json:"replace,omitempty"`
	// Wait indicates whether to wait for the release to be deployed or not.
	// +optional
	Wait bool `json:"wait,omitempty"`
	// WaitForJobs indicates whether to wait for completion of release Jobs before marking the release as successful.
	// 'Wait' has to be specified for this to take effect.
	// The timeout may be specified via the 'Timeout' field.
	WaitForJobs bool `json:"waitForJobs,omitempty"`
	// DependencyUpdate indicates whether to update the chart release if the dependencies have changed.
	// +optional
	DependencyUpdate bool `json:"dependencyUpdate,omitempty"`
	// Timeout configures the time to wait for any individual Kubernetes operation (like Jobs for hooks).
	// +optional
	Timeout time.Duration `json:"timeout,omitempty"`
	// GenerateName indicates that the release name should be generated.
	// +optional
	GenerateName bool `json:"generateName,omitempty"`
	// NameTemplate is the template used to generate the release name if GenerateName is configured.
	// +optional
	NameTemplate string `json:"nameTemplate,omitempty"`
	// Atomic indicates whether to install resources atomically.
	// 'Wait' will automatically be set to true when using Atomic.
	// +optional
	Atomic bool `json:"atomic,omitempty"`
	// SkipCRDs indicates whether to skip CRDs during installation.
	// +optional
	SkipCRDs bool `json:"skipCRDs,omitempty"`
	// Upgrade indicates whether to perform a CRD upgrade during installation.
	// +optional
	UpgradeCRDs bool `json:"upgradeCRDs,omitempty"`
	// SubNotes indicates whether to print sub-notes.
	// +optional
	SubNotes bool `json:"subNotes,omitempty"`
	// Force indicates whether to force the operation.
	// +optional
	Force bool `json:"force,omitempty"`
	// ResetValues indicates whether to reset the values.yaml file during installation.
	// +optional
	ResetValues bool `json:"resetValues,omitempty"`
	// ReuseValues indicates whether to reuse the values.yaml file during installation.
	// +optional
	ReuseValues bool `json:"reuseValues,omitempty"`
	// Recreate indicates whether to recreate the release if it already exists.
	// +optional
	Recreate bool `json:"recreate,omitempty"`
	// MaxHistory limits the maximum number of revisions saved per release.
	// +optional
	MaxHistory int `json:"maxHistory,omitempty"`
	// CleanupOnFail indicates whether to cleanup the release on failure.
	// +optional
	CleanupOnFail bool `json:"cleanupOnFail,omitempty"`
	// DryRun indicates whether to perform a dry run.
	// +optional
	DryRun bool `json:"dryRun,omitempty"`
	// Description specifies a custom description for the uninstalled release
	// +optional
	Description string `json:"description,omitempty"`
	// KeepHistory indicates whether to retain or purge the release history during uninstall
	// +optional
	KeepHistory bool `json:"keepHistory,omitempty"`
}

// A shelter of vines or branches or of latticework covered with climbing
// shrubs or vines, also latin for tree
type HelmPackage struct {
	RepoEntry repoEntry `json:"repoEntry"`
	ChartSpec chartSpec `json:"chartSpec"`
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:Schemaless
	// +kubebuilder:pruning:PreserveUnknownFields
	// +kubebuilder:validation:Type=object
	// TODO ChartValues json.RawMessage `json:"chartValues"`
	ChartValues chartutil.Values `json:"chartValues"`
	// +kubebuilder:validation:Optional
	ReleaseName string `json:"releaseName"`
}

type Pipeline []HelmPackage
