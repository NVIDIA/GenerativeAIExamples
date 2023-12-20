package storage_test

import (
	"context"
	"testing"

	"github.com/golang/mock/gomock"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/openshift-psap/special-resource-operator/pkg/clients"
	"github.com/openshift-psap/special-resource-operator/pkg/storage"
	v1 "k8s.io/api/core/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/types"
)

const (
	namespaceName = "test-ns"
	resourceName  = "test-resource"
)

var (
	ctrl       *gomock.Controller
	mockClient *clients.MockClientsInterface
	notFound   = k8serrors.NewNotFound(v1.Resource("configmap"), resourceName)
	nsn        = types.NamespacedName{Namespace: namespaceName, Name: resourceName}
	cmMatcher  = gomock.AssignableToTypeOf(&v1.ConfigMap{})
)

func TestStorage(t *testing.T) {
	RegisterFailHandler(Fail)

	BeforeEach(func() {
		ctrl = gomock.NewController(GinkgoT())
		mockClient = clients.NewMockClientsInterface(ctrl)
	})

	AfterEach(func() {
		ctrl.Finish()
	})

	RunSpecs(t, "Storage Suite")
}

var _ = Describe("storage_CheckConfigMapEntry", func() {
	const key = "test-key"

	It("should return an error with no ConfigMap present", func() {
		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{}).
			Return(notFound)

		_, err := storage.NewStorage(mockClient).CheckConfigMapEntry(context.TODO(), key, nsn)
		Expect(err).To(HaveOccurred())
	})

	It("should not return an error with an empty ConfigMap", func() {
		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{})

		_, err := storage.NewStorage(mockClient).CheckConfigMapEntry(context.TODO(), key, nsn)
		Expect(err).NotTo(HaveOccurred())
	})

	It("should return the expected value with a good ConfigMap", func() {
		const data = "test-data"

		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{}).
			Do(func(_ context.Context, _ types.NamespacedName, cm *v1.ConfigMap) {
				cm.Data = map[string]string{key: data}
			})

		v, err := storage.NewStorage(mockClient).CheckConfigMapEntry(context.TODO(), key, nsn)

		Expect(err).NotTo(HaveOccurred())
		Expect(v).To(Equal(data))
	})
})

var _ = Describe("UpdateConfigMapEntry", func() {
	It("should return an error when the ConfigMap does not exist", func() {
		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{}).
			Return(notFound)

		err := storage.NewStorage(mockClient).UpdateConfigMapEntry(context.TODO(), "any-key", "any-value", nsn)
		Expect(err).To(HaveOccurred())
	})

	It("set a key that does not already exist", func() {
		const (
			key   = "key"
			value = "value"
		)

		gomock.InOrder(
			mockClient.EXPECT().Get(context.TODO(), nsn, &v1.ConfigMap{}),
			mockClient.EXPECT().
				Update(context.TODO(), cmMatcher).
				Do(func(_ context.Context, cm *v1.ConfigMap) {
					Expect(cm.Data).To(HaveKeyWithValue(key, value))
				}),
		)

		err := storage.NewStorage(mockClient).UpdateConfigMapEntry(context.TODO(), key, value, nsn)
		Expect(err).NotTo(HaveOccurred())
	})

	It("set a key that already exists", func() {
		const (
			key      = "key"
			newValue = "new-value"
		)

		gomock.InOrder(
			mockClient.EXPECT().
				Get(context.TODO(), nsn, &v1.ConfigMap{}).
				Do(func(_ context.Context, _ types.NamespacedName, cm *v1.ConfigMap) {
					cm.Data = map[string]string{key: "oldvalue"}
				}),
			mockClient.EXPECT().
				Update(context.TODO(), cmMatcher).
				Do(func(_ context.Context, cm *v1.ConfigMap) {
					Expect(cm.Data).To(HaveKeyWithValue(key, newValue))
				}),
		)

		err := storage.NewStorage(mockClient).UpdateConfigMapEntry(context.TODO(), key, newValue, nsn)
		Expect(err).NotTo(HaveOccurred())
	})
})

var _ = Describe("DeleteConfigMapEntry", func() {
	It("should return an error when the ConfigMap does not exist", func() {
		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{}).
			Return(notFound)

		err := storage.NewStorage(mockClient).DeleteConfigMapEntry(context.TODO(), "any-key", nsn)
		Expect(err).To(HaveOccurred())
	})

	It("should not return an error when the key does not exist", func() {
		mockClient.
			EXPECT().
			Get(context.TODO(), nsn, &v1.ConfigMap{})

		err := storage.NewStorage(mockClient).DeleteConfigMapEntry(context.TODO(), "some-other-key", nsn)
		Expect(err).NotTo(HaveOccurred())
	})

	It("should delete the key when the key exists", func() {
		const (
			key      = "key"
			otherKey = "other-key"
			value    = "value"
		)

		data := map[string]string{key: value, otherKey: "other-value"}

		gomock.InOrder(
			mockClient.EXPECT().
				Get(context.TODO(), nsn, &v1.ConfigMap{}).
				Do(func(_ context.Context, _ types.NamespacedName, cm *v1.ConfigMap) {
					cm.Data = data
				}),
			mockClient.EXPECT().
				Update(context.TODO(), cmMatcher).
				Do(func(_ context.Context, cm *v1.ConfigMap) {
					Expect(cm.Data).NotTo(HaveKey(otherKey))
					Expect(cm.Data).To(HaveKeyWithValue(key, value))
				}),
		)

		err := storage.NewStorage(mockClient).DeleteConfigMapEntry(context.TODO(), otherKey, nsn)
		Expect(err).NotTo(HaveOccurred())
	})
})
