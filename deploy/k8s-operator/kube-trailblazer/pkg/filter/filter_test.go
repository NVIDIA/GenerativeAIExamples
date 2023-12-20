package filter

import (
	"context"
	"testing"

	"github.com/golang/mock/gomock"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/types"
	appsv1 "k8s.io/api/apps/v1"
	"sigs.k8s.io/controller-runtime/pkg/event"

	"github.com/openshift-psap/special-resource-operator/api/v1beta1"
	"github.com/openshift-psap/special-resource-operator/pkg/kernel"
	"github.com/openshift-psap/special-resource-operator/pkg/lifecycle"
	"github.com/openshift-psap/special-resource-operator/pkg/storage"
	operatorv1 "github.com/openshift/api/operator/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

var (
	ctrl          *gomock.Controller
	mockLifecycle *lifecycle.MockLifecycle
	mockStorage   *storage.MockStorage
	mockKernel    *kernel.MockKernelData
	f             filter
)

func TestFilter(t *testing.T) {
	RegisterFailHandler(Fail)

	BeforeEach(func() {
		ctrl = gomock.NewController(GinkgoT())
		mockLifecycle = lifecycle.NewMockLifecycle(ctrl)
		mockStorage = storage.NewMockStorage(ctrl)
		mockKernel = kernel.NewMockKernelData(ctrl)
		f = filter{
			//log: zap.New(zap.WriteTo(ioutil.Discard)),
			//lifecycle:  mockLifecycle,
			//storage:    mockStorage,
			//kernelData: mockKernel,
		}
	})

	AfterEach(func() {
		ctrl.Finish()
	})

	RunSpecs(t, "Filter Suite")
}

var _ = Describe("IsTrailblazer", func() {
	DescribeTable(
		"should return the correct value",
		func(obj client.Object, m types.GomegaMatcher) {
			Expect(f.isHelmPipelineObject(obj)).To(m)
		},
		Entry(
			Kind,
			&v1beta1.SpecialResource{
				TypeMeta: metav1.TypeMeta{Kind: Kind},
			},
			BeTrue(),
		),
		Entry(
			"Pod owned by SRO",
			&corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{OwnedLabel: "true"},
				},
			},
			BeFalse(),
		),
		Entry(
			"valid selflink",
			func() *unstructured.Unstructured {
				uo := &unstructured.Unstructured{}
				uo.SetSelfLink("/apis/sro.openshift.io/v1")

				return uo
			}(),
			BeTrue(),
		),
		Entry(
			"selflink in Label",
			func() *unstructured.Unstructured {
				uo := &unstructured.Unstructured{}
				uo.SetLabels(map[string]string{"some-label": "/apis/sro.openshift.io/v1"})

				return uo
			}(),
			BeTrue(),
		),
		Entry(
			"no selflink",
			&unstructured.Unstructured{},
			BeFalse(),
		),
	)
})

var _ = Describe("Owned", func() {
	DescribeTable(
		"should return the expected value",
		func(obj client.Object, m types.GomegaMatcher) {
			Expect(f.isOwned(obj)).To(m)
		},
		Entry(
			"via ownerReferences",
			&corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					OwnerReferences: []metav1.OwnerReference{
						{Kind: Kind},
					},
				},
			},
			BeTrue(),
		),
		Entry(
			"via labels",
			&corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{OwnedLabel: "whatever"},
				},
			},
			BeTrue(),
		),
		Entry(
			"not owned",
			&corev1.Pod{},
			BeFalse(),
		),
	)
})

var _ = Describe("Predicate", func() {
	Context("CreateFunc", func() {
		DescribeTable(
			"should work as expected",
			func(obj client.Object, m types.GomegaMatcher) {
				ret := f.GetPredicates().Create(event.CreateEvent{Object: obj})

				Expect(ret).To(m)
				Expect(f.GetMode()).To(Equal("CREATE"))
			},
			Entry(
				"special resource",
				&v1beta1.SpecialResource{},
				BeTrue(),
			),
			Entry(
				"owned",
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
					},
				},
				BeTrue(),
			),
			Entry(
				"random pod",
				&corev1.Pod{},
				BeFalse(),
			),
			Entry(
				"unmanaged special resource",
				&v1beta1.SpecialResource{
					TypeMeta: metav1.TypeMeta{Kind: Kind},
					Spec: v1beta1.SpecialResourceSpec{
						ManagementState: operatorv1.Unmanaged,
					},
				},
				BeFalse(),
			),
		)
	})

	Context("UpdateFunc", func() {
		DescribeTable(
			"should work as expected",
			func(mockSetup func(), old client.Object, new client.Object, m types.GomegaMatcher) {
				mockSetup()

				ret := f.GetPredicates().Update(event.UpdateEvent{
					ObjectOld: old,
					ObjectNew: new,
				})

				Expect(ret).To(m)
				Expect(f.GetMode()).To(Equal("UPDATE"))
			},
			Entry(
				"No change to object's Generation or ResourceVersion",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(false)
				},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				BeFalse(),
			),
			Entry(
				"Object's Generation changed, no change to ResourceVersion",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(false)
				},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      2,
						ResourceVersion: "dummy1",
					},
				},
				BeFalse(),
			),
			Entry(
				"Object has changed but is not owned by SRO",
				func() {},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						Generation:      2,
						ResourceVersion: "dummy2",
					},
				},
				BeFalse(),
			),
			Entry(
				"Object has changed and it's a SRO owned DaemonSet",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(true)
					mockLifecycle.EXPECT().UpdateDaemonSetPods(context.TODO(), gomock.Any())
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      2,
						ResourceVersion: "dummy2",
					},
				},
				BeTrue(),
			),
			Entry(
				"Object is a SRO owned & kernel affine DaemonSet, but did not change",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(true)
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Annotations: map[string]string{
							"specialresource.openshift.io/kernel-affine": "true",
						},
						Generation:      0,
						ResourceVersion: "dummy",
					},
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Annotations: map[string]string{
							"specialresource.openshift.io/kernel-affine": "true",
						},
						Generation:      0,
						ResourceVersion: "dummy",
					},
				},
				BeFalse(),
			),
			Entry(
				"Object is a SRO owned & kernel affine DaemonSet",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(true)
					mockLifecycle.EXPECT().UpdateDaemonSetPods(context.TODO(), gomock.Any())
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Annotations: map[string]string{
							"specialresource.openshift.io/kernel-affine": "true",
						},
						Generation:      0,
						ResourceVersion: "dummy",
					},
				},
				&appsv1.DaemonSet{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Annotations: map[string]string{
							"specialresource.openshift.io/kernel-affine": "true",
						},
						Generation:      1,
						ResourceVersion: "dummy",
					},
				},
				BeTrue(),
			),
			Entry(
				"Object is a SpecialResource with both Generation and ResourceVersion changed",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(false)
				},
				&v1beta1.SpecialResource{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&v1beta1.SpecialResource{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      2,
						ResourceVersion: "dummy2",
					},
				},
				BeTrue(),
			),
			Entry(
				"Object is a SpecialResource with both Generation and ResourceVersion changed but unmanaged state",
				func() {
					mockKernel.EXPECT().IsObjectAffine(gomock.Any()).Return(false)
				},
				&v1beta1.SpecialResource{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      1,
						ResourceVersion: "dummy1",
					},
				},
				&v1beta1.SpecialResource{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
						Generation:      2,
						ResourceVersion: "dummy2",
					},
					Spec: v1beta1.SpecialResourceSpec{
						ManagementState: operatorv1.Unmanaged,
					},
				},
				BeFalse(),
			),
		)
	})

	Context("DeleteFunc", func() {
		DescribeTable(
			"should work as expected",
			func(obj client.Object, m types.GomegaMatcher) {
				ret := f.GetPredicates().Delete(event.DeleteEvent{Object: obj})

				Expect(ret).To(m)
				Expect(f.GetMode()).To(Equal("DELETE"))
			},
			Entry(
				"special resource",
				&v1beta1.SpecialResource{},
				BeTrue(),
			),
			// TODO(qbarrand) testing this function requires injecting a fake pkg/storage
			//Entry("owned", ...),
			Entry(
				"random pod",
				&corev1.Pod{},
				BeFalse(),
			),
		)
	})

	Context("GenericFunc", func() {
		DescribeTable(
			"should return the correct value",
			func(obj client.Object, m types.GomegaMatcher) {
				ret := f.GetPredicates().Generic(event.GenericEvent{Object: obj})

				Expect(ret).To(m)
				Expect(f.GetMode()).To(Equal("GENERIC"))
			},
			Entry(
				"special resource",
				&v1beta1.SpecialResource{},
				BeTrue(),
			),
			Entry(
				"owned",
				&corev1.Pod{
					ObjectMeta: metav1.ObjectMeta{
						OwnerReferences: []metav1.OwnerReference{
							{Kind: Kind},
						},
					},
				},
				BeTrue(),
			),
			Entry(
				"random pod",
				&corev1.Pod{},
				BeFalse(),
			),
			Entry(
				"unmanaged special resource",
				&v1beta1.SpecialResource{
					TypeMeta: metav1.TypeMeta{Kind: Kind},
					Spec: v1beta1.SpecialResourceSpec{
						ManagementState: operatorv1.Unmanaged,
					},
				},
				BeFalse(),
			),
		)
	})
})
