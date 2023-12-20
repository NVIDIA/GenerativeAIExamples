package helmer

import (
	"bytes"
	"context"
	"encoding/json"
	"log"
	"os"
	"reflect"

	apierrors "k8s.io/apimachinery/pkg/api/errors"

	helmclient "github.com/mittwald/go-helm-client"
	"github.com/nvidia/kube-trailblazer/pkg/clients"
	"github.com/nvidia/kube-trailblazer/pkg/utils"
	"github.com/pkg/errors"
	"helm.sh/helm/v3/pkg/action"
	"helm.sh/helm/v3/pkg/chart"
	"helm.sh/helm/v3/pkg/chartutil"
	"helm.sh/helm/v3/pkg/release"
	"helm.sh/helm/v3/pkg/repo"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/klog/v2"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/yaml"
)

const (
	FilterKind       = "HelmPipeline"
	FilterOwnedLabel = "app.trailblazer.nvidia.com/owned-by"
)

func (h *Helmer) GetClientsWithRestConf(restConf *rest.Config) error {

	var err error

	opt := &helmclient.RestConfClientOptions{
		Options: &helmclient.Options{
			Namespace:        h.Package.ChartSpec.Namespace, // Change this to the namespace you wish to install the chart in.
			RepositoryCache:  "/tmp/.helmcache",
			RepositoryConfig: "/tmp/.helmrepo",
			Debug:            true,
			Linting:          false, // Change this to false if you don't want linting.
			DebugLog:         klog.Infof,
		},
		RestConfig: restConf,
	}

	h.Client, err = helmclient.NewClientFromRestConf(opt)
	if err != nil {
		return errors.Wrap(err, "\n[GGetClientWithRestConf]\tcannot create client from restConfig")
	}
	h.KubeClient, err = clients.NewKubeClientsFromRestConf(restConf)
	if err != nil {
		return errors.Wrapf(err, "\n[GGetClientWithRestConf]\tcannot create kubeClients from restConfig")
	}
	return nil
}

// GetClientWithKubeConf create a Helmer with a supplied KubeConf
func (h *Helmer) GetClientsWithKubeConf(path string, kubeContext string) error {

	if path == "" {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return errors.Wrapf(err, "\n[GetClientWithKubeConf]\tcannot read user home dir")
		}
		path = homeDir + "/.kube/config"
	}

	kubeConfig, err := os.ReadFile(path)
	if err != nil {
		return errors.Wrapf(err, "\n[GetClientWithKubeConf]\tcannot read kubeConfig from path %s:%v", path, err)
	}

	opt := &helmclient.KubeConfClientOptions{
		Options: &helmclient.Options{
			Namespace:        h.Package.ChartSpec.Namespace, // Change this to the namespace you wish to install the chart in.
			RepositoryCache:  "/tmp/.helmcache",
			RepositoryConfig: "/tmp/.helmrepo",
			Debug:            true,
			Linting:          false, // Change this to false if you don't want linting.
			DebugLog:         klog.Infof,
		},
		KubeContext: kubeContext,
		KubeConfig:  kubeConfig,
	}

	h.Client, err = helmclient.NewClientFromKubeConf(opt)
	if err != nil {
		return errors.Wrap(err, "\n[GetClientWithKubeConf]\tcannot create client from kubeConfig")
	}

	clientCfg, err := clientcmd.NewClientConfigFromBytes(kubeConfig)
	if err != nil {
		log.Fatal(err)
	}

	restConf, err := clientCfg.ClientConfig()
	if err != nil {
		log.Fatal(err)
	}
	h.KubeClient, err = clients.NewKubeClientsFromRestConf(restConf)
	if err != nil {
		return errors.Wrapf(err, "\n[GGetClientWithRestConf]\tcannot create kubeClients from restConfig")
	}
	return nil
}

// New creates a simple Helmer object with debugging flag set
func New() (*Helmer, error) {

	h := &Helmer{
		Debug: false,
	}

	os.Setenv("HELM_DEBUG", "1")
	//os.Setenv("HELM_PLUGINS", "/tmp/.helmplugins")

	if debug := os.Getenv("HELMER_DEBUG"); debug == "1" {
		h.Debug = true
	}

	h.Options = helmclient.GenericHelmOptions{
		PostRenderer: h,
		RollBack:     nil,
	}

	return h, nil
}

// NewWithPackage creates a very simple Helmer object
func NewWithPackage(pkg *HelmPackage) (*Helmer, error) {

	h, _ := New()
	h.Package = *pkg

	// TODO: Is there a better place to have this logic? BEGIN
	hash, err := utils.FNV64a(h.Package.RepoEntry.URL)
	if err != nil {
		return nil, errors.Wrapf(err, "[NewWithPackage] cannot create hash for repo ")
	}

	if h.Package.RepoEntry.Name == "" {
		h.Package.RepoEntry.Name = hash
	}

	if h.Package.ChartSpec.Namespace == "" {
		h.Package.ChartSpec.Namespace = h.Package.ChartSpec.ChartName
		h.Package.ChartSpec.CreateNamespace = true
	}

	if h.Package.ChartSpec.ReleaseName == "" {
		h.Package.ChartSpec.ReleaseName = h.Package.ChartSpec.ChartName + "-" + hash
	}
	// Replace the chart name with the full chart name
	h.Package.ChartSpec.ChartName = h.Package.RepoEntry.Name + "/" + h.Package.ChartSpec.ChartName
	// TODO: Is there a better place to have this logic? END

	// This is needed for housekeeping between rootChart and childChart
	h.Package.ReleaseName = h.Package.ChartSpec.ReleaseName

	return h, nil
}

// LoadPipeline loads an Pipeline from various sources
func LoadPipeline(object interface{}) (Pipeline, error) {

	var err error
	var pipeline Pipeline
	switch t := object.(type) {
	case string:

		klog.Info("Pipeline:", object)
		if pipeline, err = LoadPipelineFromFile(t); err != nil {
			return nil, errors.Wrapf(err, "\n[LoadPipeline]\tfailed loading Package from file: %s", t)
		}
		return pipeline, nil

	case map[string]interface{}:

		klog.Info("Pipeline:", object)
		if pipeline, err = LoadPipelineFromObject(t); err != nil {
			return nil, errors.Wrapf(err, "\n[LoadPipeline]\tfailed loading Package from map: %v", t)
		}

		return pipeline, nil

	default:
		return nil, errors.New("\n[Load]\tcannot construct Package from type: " + reflect.TypeOf(object).String())
	}
}

// LoadPipelineFromFile reads an Pipeline object from provided YANL file
func LoadPipelineFromFile(file string) (Pipeline, error) {

	var orhcard Pipeline

	yamlText, err := os.ReadFile(file)
	if err != nil {
		return nil, errors.Wrapf(err, "\n[LoadPackageFromFile]\tcannot read %s from path %s:%v", yamlText, file, err)
	}

	jsonText, err := yaml.YAMLToJSON(yamlText)
	if err != nil {
		return nil, errors.Wrapf(err, "\n[LoadPackageFromFile]\tfailed on %s", yamlText)
	}
	dec := json.NewDecoder(bytes.NewReader(jsonText))
	dec.DisallowUnknownFields()

	if err := dec.Decode(&orhcard); err != nil {
		return nil, errors.Wrapf(err, "\n[LoadPackageFromFile]\tfailed on %s", jsonText)
	}
	return UpdatePipelineWithDefaultChartSpec(orhcard), err
}

// LoadPipelineFromObject loads an Pipeline from a CR or any other YAML like object
func LoadPipelineFromObject(object map[string]interface{}) (Pipeline, error) {

	var pipeline Pipeline

	UpdatePipelineWithDefaultChartSpec(pipeline)
	return pipeline, nil
}

// GetChart loads the chart from the repo
func (h *Helmer) GetChart(chartSpec *helmclient.ChartSpec) (*chart.Chart, error) {

	chart, _, err := h.Client.GetChart(chartSpec.ChartName, &action.ChartPathOptions{})
	return chart, err

}

// InstallOrUpgradePackage implements HelmHelper
func (h *Helmer) InstallOrUpgradePackage() error {

	// The graph chart values can override chart.Values
	rootValues := h.Package.ChartValues

	chartSpec := h.Package.ChartSpec.DeepCopy()
	rootChart, err := h.GetChart(chartSpec)
	if err != nil {
		return errors.Wrapf(err, "\n[InstallOrUpgradePackage]\tcannot get Chart from Package %s", h.Package.ChartSpec.ReleaseName)
	}
	err = h.install(rootChart, &rootValues)
	if err != nil {
		return errors.Wrapf(err, "\n[InstallOrUpgradePackage]\tcannot install Chart from Package %s", h.Package.ChartSpec.ReleaseName)
	}

	return nil
}

func checkKubeAPIErrors(err error, msg string) error {
	if apierrors.IsNotFound(err) {
		return errors.Wrapf(err, "[checkKubeAPIErrors]\t%s not found", msg)

	}
	if apierrors.IsForbidden(err) {
		return errors.Wrapf(err, "[checkKubeAPIErrors]\tforbidden, check Role, ClusterRole and Bindings for operator")
	}

	if err != nil {
		return errors.Wrapf(err, "[checkKubeAPIErrors]\tunexpected error")
	}
	return nil
}

func (h *Helmer) setReleaseOwnerReference(chartRelease *release.Release) error {

	matchingLabels := map[string]string{
		"owner":  "helm",
		"name":   chartRelease.Name,
		"status": "deployed",
	}

	opts := []client.ListOption{
		client.InNamespace(chartRelease.Namespace),
		client.MatchingLabels(matchingLabels),
	}

	secrets := unstructured.UnstructuredList{}
	secrets.SetAPIVersion("v1")
	secrets.SetKind("SecretList")

	err := h.KubeClient.List(context.TODO(), &secrets, opts...)
	if checkKubeAPIErrors(err, "SecretList"); err != nil {
		return errors.Wrapf(err, "[setReleaseOwnerReference]\tcannot list secrets for chartRelease: ", chartRelease.Name)
	}

	for _, secret := range secrets.Items {
		labels := secret.GetLabels()
		labels[FilterOwnedLabel] = FilterKind

		secret.SetLabels(labels)
		klog.Infof("[setReleaseOwnerReference]\tupdating release %s:%s", secret.GetNamespace(), secret.GetName())
		err := h.KubeClient.Update(context.Background(), &secret)
		if checkKubeAPIErrors(err, "Secret"); err != nil {
			return errors.Wrapf(err, "[setReleaseOwnerReference]\tcannot update secret for chartRelease: ", chartRelease.Name)
		}
	}

	return nil
}

func (h *Helmer) install(rootChart *chart.Chart, rootValues *chartutil.Values) error {

	var err error
	// TODO: Sharing Templates with Subcharts
	// Parent charts and subcharts can share templates.
	// Any defined block in any chart is available to other charts.
	//for _, childChart := range rootChart {
	//	id := childChart.ChartFullPath()
	//}

	// rootValues will hold the value overrides for the child chart
	*rootValues, err = chartutil.CoalesceValues(rootChart, rootValues.AsMap())
	if err != nil {
		return errors.Wrapf(err, "\n[Install]\tcoalesce values failed %v", rootChart.Name())
	}

	err = chartutil.ProcessDependencies(rootChart, *rootValues)
	if err != nil {
		return errors.Wrapf(err, "\n[Install]\tprocess dependencies failed for %v", rootChart.Name())
	}

	// We need the initial releaseName since we're updating each child chart
	// with a new releaseName, this way we are not concat relase + child0 + child1
	h.installDependencies(rootChart.Dependencies(), rootValues)

	// Reset the releasename if we are the original root chart
	if rootChart.IsRoot() {
		h.Package.ChartSpec.ReleaseName = h.Package.ReleaseName
	}
	// Need to reset the root flag, helm aggregates all Values and templates
	// if it is a root chart it will only populate the child values with
	// the root .Value.childChart not the actual child values
	rootChart.NotRoot()

	vals, err := rootValues.YAML()
	if err != nil {
		return errors.Wrapf(err, "\n[Install]\tcannot convert rootValues to YAML")
	}

	h.Package.ChartSpec.ValuesYaml = vals

	chartSpec := h.Package.ChartSpec.DeepCopy()
	chartRelease, err := h.Client.InstallOrUpgradeChart(context.TODO(), chartSpec, &h.Options)
	if err != nil {
		return errors.Wrapf(err, "\n[Install]\tchart failed with %v", rootChart.Name())
	}

	err = h.setReleaseOwnerReference(chartRelease)
	if err != nil {
		return errors.Wrapf(err, "\n[Install]\tcannot setReleaseOwnerReference for charRelease %s", chartRelease.Name)
	}

	return nil
}

func (h *Helmer) installDependencies(rootChart []*chart.Chart, rootValues *chartutil.Values) error {

	childValues := chartutil.Values{}

	for _, childChart := range rootChart {

		// Overriding Values from a Parent Values
		// The value at the top level can override the
		// value of the subchart.
		if rootOverride, err := rootValues.Table(childChart.Name()); err == nil {
			childValues = chartutil.CoalesceTables(childValues, rootOverride)
		}

		// Global Chart Values
		// Global values are values that can be accessed from any
		// chart or subchart by exactly the same name.
		if rootGlobal, err := rootValues.Table("global"); err == nil {
			childGlobal, err := childValues.Table("global")
			if err != nil {
				return errors.Wrap(err, "\n[installDependencies]\tcannot extract global from childValues")
			}
			childValues["global"] = chartutil.CoalesceTables(childGlobal, rootGlobal)
		}

		h.installDependency(childChart, &childValues)
	}
	return nil
}

func (h *Helmer) updateChildPackage(childChart *chart.Chart) {
	h.Package.ChartSpec.ReleaseName = h.Package.ReleaseName + "-" + childChart.Name()
	h.Package.ChartSpec.ChartName = h.Package.RepoEntry.Name + "/" + childChart.Name()
	h.Package.ChartSpec.Version = childChart.Metadata.Version
}

func (h *Helmer) installDependency(childChart *chart.Chart, childValues *chartutil.Values) error {

	// For each chart we create an Helmer instance with its own settings
	// this makes it easier to decouple each chart for processing and clients
	// that do not interfere with each other.

	// Copy root definitions and apply to child charts, we may think of
	// own graph definitions for child charts
	h.updateChildPackage(childChart)

	klog.Info(h.Package.ChartSpec)

	c, err := NewWithPackage(&h.Package)
	if err != nil {
		return errors.Wrapf(err, "\n[installDependency]\tcannot create new Helmer with Package %s", h.Package.ChartSpec.ReleaseName)
	}

	// TODO: add generic client which can handle "all" situations
	err = c.GetClientsWithKubeConf("", "default")
	if err != nil {
		return errors.Wrapf(err, "\n[installDependency]\tcannot get client with kubeConf")
	}

	klog.Info("[InstallChildChart]: ", childChart.Name())

	err = c.install(childChart, childValues)
	if err != nil {
		return errors.Wrapf(err, "\n[installDependency]\tcannot install chart: %s", childChart.Name())
	}
	return nil
}

// Upgrade implements HelmHelper
func (h *Helmer) Upgrade() error {
	panic("unimplemented")
}

// Lint implement HelmHelper
func (h *Helmer) Lint() error {
	chartSpec := h.Package.ChartSpec.DeepCopy()
	if err := h.Client.LintChart(chartSpec); err != nil {
		return errors.Wrap(err, "[Lint] failed linting chart")
	}
	return nil
}

// Template implement HelmHelper
func (h *Helmer) Template() error {
	var err error
	yamls := []byte{}
	chartSpec := h.Package.ChartSpec.DeepCopy()
	if yamls, err = h.Client.TemplateChart(chartSpec, nil); err != nil {
		return errors.Wrap(err, "[Template] templating failed")
	}
	if h.Debug {
		klog.Info(string(yamls))
	}

	return nil
}

// AddOrUpdateRepo implements HelmHelper
func (h *Helmer) AddOrUpdateRepo() error {

	var repoEntry repo.Entry

	h.Package.RepoEntry.DeepCopyInto(&repoEntry)
	if err := h.Client.AddOrUpdateChartRepo(repoEntry); err != nil {
		return errors.Wrapf(err, "[AddOrUpdateChartRepo] failed with repo entry %v", h.Package.RepoEntry)
	}

	return nil
}

func (h *Helmer) RunChartTests() (bool, error) {
	return h.Client.RunChartTests(h.Package.ChartSpec.ReleaseName)
}

func ReconcileDelete(pipeline Pipeline, restConf *rest.Config) error {
	for _, pkg := range UpdatePipelineWithDefaultChartSpec(pipeline) {

		// For each chart we create an Helmer instance with its own settings
		// this makes it easier to decouple each chart for processing and clients
		// that do not interfere with each other.
		h, err := NewWithPackage(&pkg)
		if err != nil {
			panic(err)
		}

		err = h.GetClientsWithRestConf(restConf)
		if err != nil {
			panic(err)
		}
		chartSpec := h.Package.ChartSpec.DeepCopy()
		err = h.UninstallRelease(chartSpec)
		if err != nil {
			return errors.Wrapf(err, "\n[ReconcileDelete]\tcannot uninstall release %s", h.Package.ChartSpec.ReleaseName)
		}
	}
	return nil
}

func ReconcileCreate(pipeline Pipeline, restConf *rest.Config) ([]*release.Release, error) {

	var releases []*release.Release

	for _, pkg := range UpdatePipelineWithDefaultChartSpec(pipeline) {
		// For each chart we create an Helmer instance with its own settings
		// this makes it easier to decouple each chart for processing and clients
		// that do not interfere with each other.
		h, err := NewWithPackage(&pkg)
		if err != nil {
			panic(err)
		}

		err = h.GetClientsWithRestConf(restConf)
		if err != nil {
			panic(err)
		}
		err = h.AddOrUpdateRepo()
		if err != nil {
			return nil, err
		}

		err = h.Lint()
		if err != nil {
			return nil, err
		}
		err = h.InstallOrUpgradePackage()
		if err != nil {
			return nil, err
		}
		ok, err := h.RunChartTests()
		if !ok {
			klog.Infof("[Reconcile]\tchart tests failed for %s", h.Package.ChartSpec.ReleaseName)
			return nil, err
		}
		if err != nil {
			klog.Infof("[Reconcile]\terror executing tests for %s", h.Package.ChartSpec.ReleaseName)

		}
		if err == nil {
			releases, err = h.ListDeployedReleases()
			if err != nil {
				return nil, err
			}
		}
	}
	return releases, nil
}

// UpdateGrapshWithDefaultChartSpec updates a HelmPackage with default ChartSpec values
func UpdatePipelineWithDefaultChartSpec(in Pipeline) Pipeline {
	var out Pipeline
	for _, pkg := range in {
		pkg.ChartSpec.CreateNamespace = true
		pkg.ChartSpec.DisableHooks = false
		pkg.ChartSpec.Replace = true
		pkg.ChartSpec.Wait = true
		pkg.ChartSpec.WaitForJobs = true
		pkg.ChartSpec.DependencyUpdate = false
		pkg.ChartSpec.Timeout = 10000000000
		pkg.ChartSpec.GenerateName = false
		pkg.ChartSpec.NameTemplate = ""
		pkg.ChartSpec.Atomic = false
		pkg.ChartSpec.SkipCRDs = false
		pkg.ChartSpec.UpgradeCRDs = true
		pkg.ChartSpec.SubNotes = false
		pkg.ChartSpec.Force = false
		pkg.ChartSpec.ResetValues = false
		pkg.ChartSpec.ReuseValues = false
		pkg.ChartSpec.Recreate = false
		// Keep this at one, otherwise we will have a lot of
		// incomplete releases because of reconciliation
		pkg.ChartSpec.MaxHistory = 0
		pkg.ChartSpec.CleanupOnFail = false
		pkg.ChartSpec.DryRun = false
		pkg.ChartSpec.Description = ""
		pkg.ChartSpec.KeepHistory = false
		out = append(out, pkg)
	}
	return out
}

func (h *Helmer) UninstallRelease(spec *helmclient.ChartSpec) error {
	return h.Client.UninstallRelease(spec)
}
func (h *Helmer) ListDeployedReleases() ([]*release.Release, error) {

	ownedReleases := make([]*release.Release, 0)

	chartReleases, err := h.Client.ListDeployedReleases()
	if err != nil {

	}
	for _, chartRelease := range chartReleases {
		if chartRelease.Labels[FilterOwnedLabel] == FilterKind {
			ownedReleases = append(ownedReleases, chartRelease)
		}

	}
	return ownedReleases, nil
}
