package controllers

import (
	"context"

	"github.com/nvidia/kube-trailblazer/api/v1alpha1"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func findRequestingHelmPipeline(a []v1alpha1.HelmPipeline, x string, by string) (int, bool) {
	for i, n := range a {
		if by == "Name" {
			if x == n.GetName() {
				return i, true
			}
		}
	}
	return -1, false
}

func (r *HelmPipelineReconciler) listHelmPipelines(ctx context.Context, req ctrl.Request) (*v1alpha1.HelmPipeline, *v1alpha1.HelmPipelineList, error) {
	helmPipelines := &v1alpha1.HelmPipelineList{}

	opts := []client.ListOption{}
	err := r.KubeClient.List(ctx, helmPipelines, opts...)
	if err != nil {
		return nil, nil, err
	}

	var idx int
	var found bool
	if idx, found = findRequestingHelmPipeline(helmPipelines.Items, req.Name, "Name"); !found {
		return nil, nil, nil
	}
	return &helmPipelines.Items[idx], helmPipelines, nil
}
