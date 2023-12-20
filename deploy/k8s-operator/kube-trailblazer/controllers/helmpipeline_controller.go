/*
Copyright 2023.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controllers

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	v1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	storagev1 "k8s.io/api/storage/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/rest"
	"k8s.io/klog/v2"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	v1alpha1 "github.com/nvidia/kube-trailblazer/api/v1alpha1"
	"github.com/nvidia/kube-trailblazer/pkg/clients"
	"github.com/nvidia/kube-trailblazer/pkg/filter"
	"github.com/nvidia/kube-trailblazer/pkg/helmer"
)

// HelmPipelineReconciler reconciles a HelmPipeline object
type HelmPipelineReconciler struct {
	client.Client
	Scheme     *runtime.Scheme
	Filter     filter.Filter
	KubeClient clients.ClientsInterface
	RestConf   *rest.Config
}

//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines/finalizers,verbs=update

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the HelmPipeline object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.14.1/pkg/reconcile
func (r *HelmPipelineReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	_ = log.FromContext(ctx)

	klog.Infof("%s -- reconciling -- request %s:%s", r.Filter.GetMode(), req.Namespace, req.Name)

	klog.Info("TODO: preflight checks")

	tb, _, err := r.listHelmPipelines(ctx, req)
	if err != nil {
		klog.Error(err, "[Reconcile]\tfailed to list HelmOrchards")
		return ctrl.Result{}, err
	}

	for {
		var ok bool
		var tb *v1alpha1.HelmPipeline

		item := filter.WorkStack["DELETE"].Pop()
		if item == nil {
			break
		}
		if tb, ok = item.(*v1alpha1.HelmPipeline); !ok {
			klog.Info(fmt.Sprintf("DEBUG WorkStack Item: %+v", item))
			//panic(errors.New("owned object is not a HelmPipeline"))
			continue

		}
		err = helmer.ReconcileDelete(tb.Spec.Pipeline, r.RestConf)
		if err != nil {
			klog.Info("SUCCESS: ReconcileDelete")
			return ctrl.Result{}, err
		}
	}

	// This happens if Helmer was reconciling and the HelmOrchard was deleted
	if tb == nil {
		klog.Info("SUCCESS: reconcile (tb == nil)")
		return ctrl.Result{}, nil
	}

	klog.Infof("[Reconcile] -- %s -- HelmPipeline %s:%s", r.Filter.GetMode(), tb.GetNamespace(), tb.GetName())
	releases, err := helmer.ReconcileCreate(tb.Spec.Pipeline, r.RestConf)
	if err != nil {
		klog.Warning(err, "[Reconcile]\trequeue request due to error")
		return ctrl.Result{Requeue: true}, nil
	}

	klog.Info("TODO: metrics")
	for _, release := range releases {
		klog.Infof("[Reconcile]\tRELEASES: %s:%s", release.Namespace, release.Name)
	}

	klog.Info("SUCCESS: reconcile")
	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *HelmPipelineReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&v1alpha1.HelmPipeline{}).
		Owns(&v1.Pod{}).
		Owns(&appsv1.DaemonSet{}).
		Owns(&appsv1.Deployment{}).
		Owns(&storagev1.CSIDriver{}).
		Owns(&v1.ConfigMap{}).
		Owns(&v1.ServiceAccount{}).
		Owns(&rbacv1.Role{}).
		Owns(&rbacv1.RoleBinding{}).
		Owns(&rbacv1.ClusterRole{}).
		Owns(&rbacv1.ClusterRoleBinding{}).
		Owns(&v1.Secret{}).
		WithEventFilter(r.Filter.GetPredicates()).
		Complete(r)
}
