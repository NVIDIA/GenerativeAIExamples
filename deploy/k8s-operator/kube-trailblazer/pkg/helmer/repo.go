package helmer

import "helm.sh/helm/v3/pkg/repo"

func (in *repoEntry) DeepCopyInto(out *repo.Entry) *repo.Entry {
	out.Name = in.Name
	out.URL = in.URL
	out.Username = in.Username
	out.Password = in.Password
	out.CertFile = in.CertFile
	out.KeyFile = in.KeyFile
	out.CAFile = in.CAFile
	out.InsecureSkipTLSverify = in.InsecureSkipTLSverify
	out.PassCredentialsAll = in.PassCredentialsAll

	return out
}
