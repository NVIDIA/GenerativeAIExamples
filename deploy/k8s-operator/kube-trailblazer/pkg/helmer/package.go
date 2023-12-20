package helmer

import (
	"github.com/mittwald/go-helm-client/values"
)

// NewHelmPackageWithDefaultChartSpec creates a new HelmPackage with default ChartSpec values
// that trailblazer things may be usefull
func NewHelmPackageWithDefaultChartSpec() *HelmPackage {
	pipeline := &HelmPackage{
		RepoEntry: repoEntry{},
		ChartSpec: chartSpec{
			ReleaseName:      "",
			ChartName:        "",
			Namespace:        "",
			ValuesYaml:       "",
			ValuesOptions:    values.Options{},
			Version:          "",
			CreateNamespace:  true,
			DisableHooks:     false,
			Replace:          true,
			Wait:             true,
			WaitForJobs:      true,
			DependencyUpdate: false,
			Timeout:          90000000000,
			GenerateName:     true,
			NameTemplate:     "",
			Atomic:           false,
			SkipCRDs:         false,
			UpgradeCRDs:      true,
			SubNotes:         false,
			Force:            false,
			ResetValues:      false,
			ReuseValues:      false,
			Recreate:         false,
			MaxHistory:       1,
			CleanupOnFail:    false,
			DryRun:           false,
			Description:      "",
			KeepHistory:      false,
		},
		ChartValues: make(map[string]interface{}),
		ReleaseName: "",
	}
	return pipeline
}

func (in *HelmPackage) DeepCopyInto(out *HelmPackage) {
	*out = *in
	out.RepoEntry = in.RepoEntry
	out.ChartSpec = in.ChartSpec
	out.ChartValues = in.ChartValues
}

func (in *HelmPackage) DeepCopy() *HelmPackage {
	if in == nil {
		return nil
	}
	out := new(HelmPackage)
	in.DeepCopyInto(out)
	return out
}
