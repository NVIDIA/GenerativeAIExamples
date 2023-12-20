package storage

import (
	"context"

	"github.com/openshift-psap/special-resource-operator/pkg/clients"
	v1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

//go:generate mockgen -source=storage.go -package=storage -destination=mock_storage_api.go

type Storage interface {
	CheckConfigMapEntry(context.Context, string, types.NamespacedName) (string, error)
	UpdateConfigMapEntry(context.Context, string, string, types.NamespacedName) error
	DeleteConfigMapEntry(context.Context, string, types.NamespacedName) error
}

type storage struct {
	kubeClient clients.ClientsInterface
}

func NewStorage(kubeClient clients.ClientsInterface) Storage {
	return &storage{kubeClient: kubeClient}
}

func (s *storage) CheckConfigMapEntry(ctx context.Context, key string, ins types.NamespacedName) (string, error) {
	cm, err := s.getConfigMap(ctx, ins.Namespace, ins.Name)
	if err != nil {
		return "", err
	}

	return cm.Data[key], nil
}

func (s *storage) UpdateConfigMapEntry(ctx context.Context, key string, value string, ins types.NamespacedName) error {
	cm, err := s.getConfigMap(ctx, ins.Namespace, ins.Name)
	if err != nil {
		ctrl.LoggerFrom(ctx).Error(err, "Failed to get configmap to update an entry", "namespacedName", ins, "key", key, "value", value)
		return err
	}

	if cm.Data == nil {
		cm.Data = make(map[string]string)
	}

	if cm.Data[key] != value {
		cm.Data[key] = value

		if err = s.updateObject(ctx, cm); err != nil {
			ctrl.LoggerFrom(ctx).Error(err, "Failed to update configmap to update an entry", "namespacedName", ins, "key", key, "value", value)
			return err
		}
	}

	return nil
}

func (s *storage) DeleteConfigMapEntry(ctx context.Context, key string, ins types.NamespacedName) error {
	cm, err := s.getConfigMap(ctx, ins.Namespace, ins.Name)
	if err != nil {
		ctrl.LoggerFrom(ctx).Error(err, "Failed to get configmap to remove an entry", "namespacedName", ins, "key", key)
		return err
	}

	if _, ok := cm.Data[key]; ok {
		delete(cm.Data, key)

		if err = s.updateObject(ctx, cm); err != nil {
			ctrl.LoggerFrom(ctx).Error(err, "Failed to update configmap to remove an entry", "namespacedName", ins, "key", key)
			return err
		}
	}

	return nil
}

func (s *storage) getConfigMap(ctx context.Context, namespace string, name string) (*v1.ConfigMap, error) {
	cm := &v1.ConfigMap{}
	dep := types.NamespacedName{Namespace: namespace, Name: name}

	err := s.kubeClient.Get(ctx, dep, cm)

	if apierrors.IsNotFound(err) {
		ctrl.LoggerFrom(ctx).Error(err, "Failed to get configmap", "cmNamespace", namespace, "cmName", name)
		return nil, err
	}

	return cm, err
}

func (s *storage) updateObject(ctx context.Context, cm client.Object) error {
	return s.kubeClient.Update(ctx, cm)
}
