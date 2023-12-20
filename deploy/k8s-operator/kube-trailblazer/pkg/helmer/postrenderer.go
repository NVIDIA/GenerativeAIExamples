package helmer

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func mkdir(path string) error {
	if _, err := os.Stat(path); errors.Is(err, os.ErrNotExist) {
		err := os.MkdirAll(path, os.ModePerm)
		if err != nil {
			return err
		}
	}
	return nil
}

func (h *Helmer) Run(renderedManifests *bytes.Buffer) (modifiedManifests *bytes.Buffer, err error) {

	kustomizePath := "/kustomize/"
	chart := h.Package.ReleaseName + "-" + h.Package.ChartSpec.Version
	basePath := kustomizePath + chart + "/base/"

	err = mkdir(basePath)
	check(err)

	var kustomization bytes.Buffer

	manifests := bytes.Split(renderedManifests.Bytes(), []byte("---"))
	if len(manifests[0]) == 0 {
		manifests = manifests[1:]
	}

	kustomization.WriteString("resources:\n")
	for i, manifest := range manifests {
		// this cannot error per docs
		name := fmt.Sprintf("resource-%d.yaml", i)
		err := os.WriteFile(basePath+name, manifest, 0644)
		check(err)
		fmt.Fprintf(&kustomization, " - %s\n", name)
	}

	kustomization.WriteString("\n")
	kustomization.WriteString("commonLabels:\n")
	kustomization.WriteString("  app.trailblazer.nvidia.com/owned-by: HelmOrchard\n")

	err = os.WriteFile(basePath+"kustomization.yaml", kustomization.Bytes(), 0644)
	check(err)

	kustomize := exec.Command("kustomize", "build", basePath)
	out, err := kustomize.Output()
	check(err)

	// otherwise, print the output from running the command
	//klog.Info("Output: ", string(out))
	renderedManifests = bytes.NewBuffer(out)

	return renderedManifests, nil
}
