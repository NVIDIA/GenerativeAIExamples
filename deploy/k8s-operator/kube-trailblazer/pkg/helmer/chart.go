package helmer

import helmclient "github.com/mittwald/go-helm-client"

func (in *chartSpec) DeepCopyInto(out *helmclient.ChartSpec) {

	// copy all chartSpec fields from out to in
	out.ReleaseName = in.ReleaseName
	out.ChartName = in.ChartName
	out.Namespace = in.Namespace
	out.ValuesYaml = in.ValuesYaml
	out.ValuesOptions = in.ValuesOptions
	out.Version = in.Version
	out.CreateNamespace = in.CreateNamespace
	out.DisableHooks = in.DisableHooks
	out.Replace = in.Replace
	out.Wait = in.Wait
	out.WaitForJobs = in.WaitForJobs
	out.DependencyUpdate = in.DependencyUpdate
	out.Timeout = in.Timeout
	out.GenerateName = in.GenerateName
	out.NameTemplate = in.NameTemplate
	out.Atomic = in.Atomic
	out.SkipCRDs = in.SkipCRDs
	out.UpgradeCRDs = in.UpgradeCRDs
	out.SubNotes = in.SubNotes
	out.Force = in.Force
	out.ResetValues = in.ResetValues
	out.ReuseValues = in.ReuseValues
	out.Recreate = in.Recreate
	out.MaxHistory = in.MaxHistory
	out.CleanupOnFail = in.CleanupOnFail
	out.DryRun = in.DryRun
	out.Description = in.Description
	out.KeepHistory = in.KeepHistory
}

func (in *chartSpec) DeepCopy() *helmclient.ChartSpec {

	var out helmclient.ChartSpec
	// copy all chartSpec fields from out to in
	out.ReleaseName = in.ReleaseName
	out.ChartName = in.ChartName
	out.Namespace = in.Namespace
	out.ValuesYaml = in.ValuesYaml
	out.ValuesOptions = in.ValuesOptions
	out.Version = in.Version
	out.CreateNamespace = in.CreateNamespace
	out.DisableHooks = in.DisableHooks
	out.Replace = in.Replace
	out.Wait = in.Wait
	out.WaitForJobs = in.WaitForJobs
	out.DependencyUpdate = in.DependencyUpdate
	out.Timeout = in.Timeout
	out.GenerateName = in.GenerateName
	out.NameTemplate = in.NameTemplate
	out.Atomic = in.Atomic
	out.SkipCRDs = in.SkipCRDs
	out.UpgradeCRDs = in.UpgradeCRDs
	out.SubNotes = in.SubNotes
	out.Force = in.Force
	out.ResetValues = in.ResetValues
	out.ReuseValues = in.ReuseValues
	out.Recreate = in.Recreate
	out.MaxHistory = in.MaxHistory
	out.CleanupOnFail = in.CleanupOnFail
	out.DryRun = in.DryRun
	out.Description = in.Description
	out.KeepHistory = in.KeepHistory

	return &out
}
