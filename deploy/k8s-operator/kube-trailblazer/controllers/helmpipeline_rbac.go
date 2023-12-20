package controllers

//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=package.nvidia.com,resources=helmpipelines/finalizers,verbs=update
//+kubebuilder:rbac:groups="",resources=nodes/status,verbs=get;list
//+kubebuilder:rbac:groups="",resources=nodes/proxy,verbs=get
//+kubebuilder:rbac:groups=nfd.k8s-sigs.io,resources=nodefeaturerules,verbs=get;list;watch
//+kubebuilder:rbac:groups=nfd.k8s-sigs.io,resources=nodefeatures,verbs=get;list;watch;delete;create;update
//+kubebuilder:rbac:groups=topology.node.k8s.io,resources=noderesourcetopologies,verbs=delete;list
//+kubebuilder:rbac:groups=networking.k8s.io, resources=clustercidrs, verbs=list;watch
//+kubebuilder:rbac:groups=nvidia.com, resources=clusterpolicies, verbs=get;list;watch;patch
