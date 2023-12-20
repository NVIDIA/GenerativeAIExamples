package main

import (
	"flag"
	"log"
	"os"

	cli "github.com/urfave/cli/v2"

	"github.com/nvidia/kube-trailblazer/pkg/helmer"
	klog "k8s.io/klog/v2"
)

func init() {
	flags := flag.FlagSet{
		Usage: func() {
		},
	}
	// Default is logtostderr
	klog.InitFlags(&flags)
}

func main() {

	var err error
	var graphs cli.StringSlice
	var kubeConfig string

	app := &cli.App{
		Name:  "helmer",
		Usage: "reconcile a helm graph",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "kubeConfig",
				Aliases:     []string{"k"},
				DefaultText: "${HOME}/.kube/config",
				Value:       "${HOME}/.kube/config",
				Destination: &kubeConfig,
			},
			&cli.StringSliceFlag{
				Name:        "graphs",
				Aliases:     []string{"g"},
				Required:    true,
				DefaultText: "None",
				Destination: &graphs,
			},
		},
		Action: func(c *cli.Context) error {
			return nil
		},
	}

	app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}

	os.Setenv("HELMER_DEBUG", "1")

	for _, fromFile := range graphs.Value() {

		var orchard helmer.Pipeline
		// We're providing Helmer a Graph as the interface what to create
		// In an operator we would have a go struct but for testing we can
		// also load a Graph from file.
		orchard, err = helmer.LoadPipeline(fromFile)
		if err != nil {
			panic(err)
		}

		// RECONCILE LOOP
		for _, arbor := range orchard {

			// For each chart we create an Helmer instance with its own settings
			// this makes it easier to decouple each chart for processing and clients
			// that do not interfere with each other.
			h, err := helmer.NewWithPackage(&arbor)
			if err != nil {
				panic(err)
			}

			err = h.GetClientsWithKubeConf("", "default")
			if err != nil {
				panic(err)
			}

			err = h.AddOrUpdateRepo()
			if err != nil {
				panic(err)
			}

			err = h.Lint()
			if err != nil {
				panic(err)
			}

			//	klog.Info("TEMPLATE")
			//	err = h.Template()
			//	if err != nil {
			//		panic(err)
			//	}

			reconcile(h)
		}

	}
	return
}

func reconcile(h *helmer.Helmer) {

	for {
		err := h.InstallOrUpgradePackage()
		if err != nil {
			klog.Info(err)
		}
		if err == nil {
			break
		}
	}
}

/*
func OpenShiftInstallOrder() {
	// Mutates helm package exported variables
	idx := utils.StringSliceFind(releaseutil.InstallOrder, "Service")
	releaseutil.InstallOrder = utils.StringSliceInsert(releaseutil.InstallOrder, idx, "BuildConfig")
	releaseutil.InstallOrder = utils.StringSliceInsert(releaseutil.InstallOrder, idx, "ImageStream")
	releaseutil.InstallOrder = utils.StringSliceInsert(releaseutil.InstallOrder, idx, "SecurityContextConstraints")
	releaseutil.InstallOrder = utils.StringSliceInsert(releaseutil.InstallOrder, idx, "Issuer")
	releaseutil.InstallOrder = utils.StringSliceInsert(releaseutil.InstallOrder, idx, "Certificates")
}
*/
