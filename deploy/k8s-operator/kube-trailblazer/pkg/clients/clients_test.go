package clients

import (
	"context"
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"

	"github.com/openshift-psap/special-resource-operator/pkg/utils"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestPkgClients(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Clients Suite")
}

var _ = Describe("GetNodesByLabels", func() {
	type testInput struct {
		numNodes         int
		labels           map[string]string
		addTaint         bool
		taintEffect      corev1.TaintEffect
		expectedNumNodes int
	}

	DescribeTable(
		"should return correct number of nodes",
		func(test testInput) {
			nodesList := utils.CreateNodesList(test.numNodes, test.labels)
			if test.addTaint {
				utils.SetTaint(&nodesList.Items[0], "taintKey", "taintValue", test.taintEffect)
			}
			objs := []runtime.Object{nodesList}
			clientsStruct := k8sClients{runtimeClient: fake.NewClientBuilder().WithRuntimeObjects(objs...).Build()}
			res, _ := clientsStruct.GetNodesByLabels(context.TODO(), test.labels)
			Expect(res.Items).To(HaveLen(test.expectedNumNodes))
		},
		Entry(
			"all nodes without taint",
			testInput{
				numNodes:         3,
				labels:           map[string]string{"key1": "label1"},
				addTaint:         false,
				expectedNumNodes: 3,
			},
		),
		Entry(
			"a node with NoExecute taint",
			testInput{
				numNodes:         3,
				labels:           map[string]string{"key1": "label1"},
				addTaint:         true,
				taintEffect:      corev1.TaintEffectNoExecute,
				expectedNumNodes: 2,
			},
		),
		Entry(
			"a node with NoSchedule taint",
			testInput{
				numNodes:         3,
				labels:           map[string]string{"key1": "label1"},
				addTaint:         true,
				taintEffect:      corev1.TaintEffectNoSchedule,
				expectedNumNodes: 2,
			},
		),
	)
})
