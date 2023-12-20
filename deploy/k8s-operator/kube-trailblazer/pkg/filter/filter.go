package filter

import (
	"github.com/nvidia/kube-trailblazer/api/v1alpha1"
	operatorv1 "github.com/openshift/api/operator/v1"
	"golang.design/x/lockfree"
	"k8s.io/klog/v2"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
)

const (
	Kind       = "HelmPipeline"
	OwnedLabel = "app.trailblazer.nvidia.com/owned-by"
)

var (
	WorkStack = make(map[string]*lockfree.Stack)
)

type Filter interface {
	GetPredicates() predicate.Predicate
	GetMode() string
}

func NewFilter() Filter {
	WorkStack["DELETE"] = lockfree.NewStack()
	return &filter{
		//log: log.WithName("filter"),
		//lifecycle:  lifecycle,
		//storage: storage,
		//kernelData: kernelData,
	}
}

type filter struct {
	mode string
}

func (f *filter) GetMode() string {
	return f.mode
}

func (f *filter) isTrailblazerUnmanaged(obj client.Object) bool {
	tb, ok := obj.(*v1alpha1.HelmPipeline)
	if !ok {
		return false
	}
	return tb.Spec.ManagementState == operatorv1.Unmanaged
}

func (f *filter) isHelmPipelineObject(obj client.Object) bool {

	_, ok := obj.(*v1alpha1.HelmPipeline)
	return ok
}

func (f *filter) isOwned(obj client.Object) bool {

	for _, owner := range obj.GetOwnerReferences() {
		if owner.Kind == Kind {
			return true
		}
	}

	var labels map[string]string

	if labels = obj.GetLabels(); labels != nil {
		if _, found := labels[OwnedLabel]; found {
			return true
		}
	}
	return false
}

func (f *filter) selectOnlyOwnedObjects(obj client.Object) bool {

	if f.isHelmPipelineObject(obj) {
		if f.isTrailblazerUnmanaged(obj) {
			return false
		}
		klog.Infof("%s - isHelmPipeline - %s -- %s:%s", f.mode, obj.GetNamespace(), obj.GetObjectKind(), obj.GetName())
		if f.mode == "DELETE" {
			WorkStack[f.mode].Push(obj)
		}
		return true
	}

	if f.isOwned(obj) {
		klog.Infof("%s - isOwned - %s -- %s:%s", f.mode, obj.GetNamespace(), obj.GetObjectKind(), obj.GetName())
		return true
	}
	return false
}

func (f *filter) GetPredicates() predicate.Predicate {
	return predicate.Funcs{
		CreateFunc: func(e event.CreateEvent) bool {

			f.mode = "CREATE"
			return f.selectOnlyOwnedObjects(e.Object)
		},

		UpdateFunc: func(e event.UpdateEvent) bool {
			// Ignore updates if the resourceVersion does not change
			// resourceVersion is updated when the object is modified

			/* UPDATING THE STATUS WILL INCREASE THE RESOURCEVERSION DISABLING
			 * BUT KEEPING FOR REFERENCE
			if e.MetaOld.GetResourceVersion() == e.MetaNew.GetResourceVersion() {
				return false
			}*/
			f.mode = "UPDATE"

			ownedObject := f.selectOnlyOwnedObjects(e.ObjectNew)
			if !ownedObject {
				return false
			}

			// Ignore updates to CR status in which case metadata.Generation does not change
			if e.ObjectOld.GetGeneration() == e.ObjectNew.GetGeneration() {
				klog.Infof("UPDATE Generation Equal %s ", e.ObjectNew.GetName())
				//return false
			}
			// Some objects will increase generation on update ...
			if e.ObjectOld.GetResourceVersion() == e.ObjectNew.GetResourceVersion() {
				klog.Infof("UPDATE ResourceVersion Equal %s", e.ObjectNew.GetName())
				//return false
			}

			// If a trailblazer dependency is updated we
			// want to reconcile it, handle the update event
			return f.selectOnlyOwnedObjects(e.ObjectNew)
		},
		DeleteFunc: func(e event.DeleteEvent) bool {

			f.mode = "DELETE"
			// If an owned object is deleted we
			// want to recreate it so handle the delete event
			return f.selectOnlyOwnedObjects(e.Object)
		},
		GenericFunc: func(e event.GenericEvent) bool {

			f.mode = "GENERIC"
			// If a owned object is modified  we
			// want to reconcile it, handle the generic event
			return f.selectOnlyOwnedObjects(e.Object)
		},
	}
}
