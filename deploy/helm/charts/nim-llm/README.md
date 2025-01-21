# NIM-LLM Helm Chart

NVIDIA NIM for LLMs Helm Chart simplifies NIM deployment on Kubernetes. It aims to support deployment with a variety of possible cluster, GPU and storage confurations.

## Setting up the environment

This helm chart requires that you have a secret with your NGC API key configured for downloading private images, and one with your NGC API key (below named ngc-api). These will likely have the same key in it, but they will have different formats (dockerconfig.json vs opaque).

To deploy a NIM, some custom values are generally required. Typically, this looks similar to this, at a minimum:

```yaml
image:
    repository: "nvcr.io/nim/meta/llama3-8b-instruct" # container location
    tag: 1.0.0 # NIM version you want to deploy
model:
  ngcAPISecret: ngc-api  # name of a secret in the cluster that includes a key named NGC_API_KEY and is an NGC API key
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    nvidia.com/gpu: 1
persistence:
  enabled: true
  size: 30Gi
imagePullSecrets:
  - name: my-image-secret # secret created to pull nvcr.io images, see https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/
```

## Storage

Storage is a particular concern when setting up NIMs. Models can be quite large, and you can fill disk downloading things to emptyDirs or other locations around your pod image. It is best to ensure you have persistent storage of some kind mounted on your 
pod.

This chart supports four general categories of storage outside of the default of an emptyDir:
  1. Persistent Volume Claims (enabled with `persistence.enabled`)
  2. Persistent Volume Claim templates (enabled with `persistence.enabled` and `statefulSet.enabled`)
  3. Direct NFS (enabled with `nfs.enabled`)
  4. hostPath (enabled with `hostPath.enabled`)

The supported options for each are detailed in relevant section of Parameters below. These options are mutually exclusive. You should only enable *one* option. They represent different strategies of cluster management and scaling that should be considered before selecting. If in doubt or just creating a single pod, use persistent volumes.

See options below.

## Parameters

### Deployment parameters

| Name                              | Description                                                                                                                                                                                  | Value   |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `affinity`                        | [default: {}] Affinity settings for deployment.                                                                                                                                              | `{}`    |
| `containerSecurityContext`        | Sets privilege and access control settings for container (Only affects the main container, not pod-level).                                                                                   | `{}`    |
| `customCommand`                   | Overrides command line options sent to the NIM with the array listed here.                                                                                                                   | `[]`    |
| `customArgs`                      | Overrides command line arguments of the NIM container with the array listed here.                                                                                                            | `[]`    |
| `env`                             | Adds arbitrary environment variables to the main container.                                                                                                                                  | `[]`    |
| `extraVolumes`                    | Adds arbitrary additional volumes to the deployment set definition.                                                                                                                          | `{}`    |
| `extraVolumeMounts`               | Adds volume mounts to the main container from `extraVolumes`.                                                                                                                                | `{}`    |
| `image.repository`                | Specifies the NIM-LLM Image to deploy.                                                                                                                                                       | `""`    |
| `image.tag`                       | Specifies the image tag or version.                                                                                                                                                          | `""`    |
| `image.pullPolicy`                | Sets the image pull policy.                                                                                                                                                                  | `""`    |
| `imagePullSecrets`                | Specifies a list of secret names that are needed for the main container and any init containers.                                                                                             |         |
| `initContainers`                  | Specifies model init containers, if needed.                                                                                                                                                  |         |
| `initContainers.ngcInit`          | Legacy containers only. Instantiate and configure an NGC init container. It should either have NGC CLI pre-installed or `wget` + `unzip` pre-installed -- must not be `musl`-based (alpine). | `{}`    |
| `initContainers.extraInit`        | Fully specify any additional init containers your use case requires.                                                                                                                         | `[]`    |
| `healthPort`                      | Specifies health check port. -- for use with `models.legacyCompat` only since current NIMs have no separate port.                                                                            | `8000`  |
| `nodeSelector`                    | Sets node selectors for the NIM -- for example `nvidia.com/gpu.present: "true"`.                                                                                                             | `{}`    |
| `podAnnotations`                  | Sets additional annotations on the main deployment pods.                                                                                                                                     | `{}`    |
| `podSecurityContext`              | Specifies security context settings for pod.                                                                                                                                                 |         |
| `podSecurityContext.runAsUser`    | Specify user UID for pod.                                                                                                                                                                    | `1000`  |
| `podSecurityContext.runAsGroup`   | Specify group ID for pod.                                                                                                                                                                    | `1000`  |
| `podSecurityContext.fsGroup`      | Specify file system owner group id.                                                                                                                                                          | `1000`  |
| `replicaCount`                    | Specify static replica count for deployment.                                                                                                                                                 | `1`     |
| `resources`                       | Specify resources limits and requests for the running service.                                                                                                                               |         |
| `resources.limits.nvidia.com/gpu` | Specify number of GPUs to present to the running service.                                                                                                                                    | `1`     |
| `serviceAccount.create`           | Specifies whether a service account should be created.                                                                                                                                       | `false` |
| `serviceAccount.annotations`      | Sets annotations to be added to the service account.                                                                                                                                         | `{}`    |
| `serviceAccount.name`             | Specifies the name of the service account to use. If it is not set and create is `true`, a name is generated using a `fullname` template.                                                    | `""`    |
| `statefulSet.enabled`             | Enables `statefulset` deployment. Enabling `statefulSet` allows PVC templates for scaling. If using central PVC with RWX `accessMode`, this isn't needed.                                    | `true`  |
| `tolerations`                     | Specify tolerations for pod assignment. Allows the scheduler to schedule pods with matching taints.                                                                                          |         |

### Autoscaling parameters

Values used for creating a `Horizontal Pod Autoscaler`. If autoscaling is not enabled, the rest are ignored.
NVIDIA recommends usage of the custom metrics API, commonly implemented with the prometheus-adapter.
Standard metrics of CPU and memory are of limited use in scaling NIM.

| Name                      | Description                               | Value   |
| ------------------------- | ----------------------------------------- | ------- |
| `autoscaling.enabled`     | Enables horizontal pod autoscaler.        | `false` |
| `autoscaling.minReplicas` | Specify minimum replicas for autoscaling. | `1`     |
| `autoscaling.maxReplicas` | Specify maximum replicas for autoscaling. | `10`    |
| `autoscaling.metrics`     | Array of metrics for autoscaling.         | `[]`    |

### Ingress parameters

| Name                                    | Description                                                                                                       | Value                    |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `ingress.enabled`                       | Enables ingress.                                                                                                  | `false`                  |
| `ingress.className`                     | Specify class name for Ingress.                                                                                   | `""`                     |
| `ingress.annotations`                   | Specify additional annotations for ingress.                                                                       | `{}`                     |
| `ingress.hosts`                         | Specify list of hosts each containing lists of paths.                                                             |                          |
| `ingress.hosts[0].host`                 | Specify name of host.                                                                                             | `chart-example.local`    |
| `ingress.hosts[0].paths[0].path`        | Specify ingress path.                                                                                             | `/`                      |
| `ingress.hosts[0].paths[0].pathType`    | Specify path type.                                                                                                | `ImplementationSpecific` |
| `ingress.hosts[0].paths[0].serviceType` | Specify service type. It can be can be `nemo` or `openai` -- make sure your model serves the appropriate port(s). | `openai`                 |
| `ingress.tls`                           | Specify list of pairs of TLS `secretName` and hosts.                                                              | `[]`                     |

### Probe parameters

| Name                                 | Description                                                              | Value              |
| ------------------------------------ | ------------------------------------------------------------------------ | ------------------ |
| `livenessProbe.enabled`              | Enables `livenessProbe``.                                                | `true`             |
| `livenessProbe.method`               | `LivenessProbe` `http` or `script`, but no script is currently provided. | `http`             |
| `livenessProbe.command`              | `LivenessProbe`` script command to use (unsupported at this time).       | `["myscript.sh"]`  |
| `livenessProbe.path`                 | `LivenessProbe`` endpoint path.                                          | `/v1/health/live`  |
| `livenessProbe.initialDelaySeconds`  | Initial delay seconds for `livenessProbe`.                               | `15`               |
| `livenessProbe.timeoutSeconds`       | Timeout seconds for `livenessProbe`.                                     | `1`                |
| `livenessProbe.periodSeconds`        | Period seconds for `livenessProbe`.                                      | `10`               |
| `livenessProbe.successThreshold`     | Success threshold for `livenessProbe`.                                   | `1`                |
| `livenessProbe.failureThreshold`     | Failure threshold for `livenessProbe`.                                   | `3`                |
| `readinessProbe.enabled`             | Enables `readinessProbe`.                                                | `true`             |
| `readinessProbe.path`                | Readiness Endpoint Path.                                                 | `/v1/health/ready` |
| `readinessProbe.initialDelaySeconds` | Initial delay seconds for `readinessProbe`.                              | `15`               |
| `readinessProbe.timeoutSeconds`      | Timeout seconds for `readinessProbe`.                                    | `1`                |
| `readinessProbe.periodSeconds`       | Period seconds for `readinessProbe`.                                     | `10`               |
| `readinessProbe.successThreshold`    | Success threshold for `readinessProbe`.                                  | `1`                |
| `readinessProbe.failureThreshold`    | Failure threshold for `readinessProbe`.                                  | `3`                |
| `startupProbe.enabled`               | Enables `startupProbe`.                                                  | `true`             |
| `startupProbe.path`                  | `StartupProbe` Endpoint Path.                                            | `/v1/health/ready` |
| `startupProbe.initialDelaySeconds`   | Initial delay seconds for `startupProbe`.                                | `40`               |
| `startupProbe.timeoutSeconds`        | Timeout seconds for `startupProbe`.                                      | `1`                |
| `startupProbe.periodSeconds`         | Period seconds for `startupProbe`.                                       | `10`               |
| `startupProbe.successThreshold`      | Success threshold for `startupProbe`.                                    | `1`                |
| `startupProbe.failureThreshold`      | Failure threshold for `startupProbe`.                                    | `180`              |

### Metrics parameters

| Name                                      | Description                                                                                                  | Value   |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------- |
| `metrics`                                 | Opens the metrics port for the triton inference server on port 8002.                                         |         |
| `metrics.enabled`                         | Enables metrics endpoint -- for `legacyCompat` only since current NIMs serve metrics on the OpenAI API port. | `true`  |
| `serviceMonitor`                          | Options for `serviceMonitor` to use the Prometheus Operator and the primary service object.                  |         |
| `metrics.serviceMonitor.enabled`          | Enables `serviceMonitor` creation.                                                                           | `false` |
| `metrics.serviceMonitor.additionalLabels` | Specify additional labels for ServiceMonitor.                                                                | `{}`    |

### Models parameters

| Name                 | Description                                                                                                                                                                                                                                                                                                                | Value                     |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `model.nimCache`     | Path to mount writeable storage or pre-filled model cache for the NIM.                                                                                                                                                                                                                                                     | `""`                      |
| `model.name`         | Specifies the name of the model in the API (usually, the name of the NIM). This is mostly used for helm tests and is usually otherwise optional. This must match the name from _/v1/models_ to allow `helm test <release-name>` to work. In `legacyCompat`, this is required and sets the name of the model in /v1/models. | `meta/llama3-8b-instruct` |
| `model.ngcAPISecret` | Name of pre-existing secret with a key named `NGC_API_KEY` that contains an API key for NGC model downloads.                                                                                                                                                                                                               | `""`                      |
| `model.ngcAPIKey`    | NGC API key literal to use as the API secret and image pull secret when set.                                                                                                                                                                                                                                               | `""`                      |
| `model.openaiPort`   | Specifies the Open AI API Port.                                                                                                                                                                                                                                                                                            | `8000`                    |
| `model.labels`       | Specifies extra labels to be added on deployed pods.                                                                                                                                                                                                                                                                       | `{}`                      |
| `model.jsonLogging`  | Turn JSON lines logging on or off. Defaults to true.                                                                                                                                                                                                                                                                       | `true`                    |
| `model.logLevel`     | Log level of NIM service. Possible values of the variable are TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL.                                                                                                                                                                                                                | `INFO`                    |

### Deprecated and Legacy Model parameters

| Name                   | Description                                                                                                                                             | Value         |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `model.legacyCompat`   | Set `true` to enable compatibility with pre-release NIM versions prior to 1.0.0.                                                                        | `false`       |
| `model.numGpus`        | (deprecated) Specify GPU requirements for the model.                                                                                                    | `1`           |
| `model.subPath`        | (deprecated) Specify path within the model volume to mount if not the root -- default works with `ngcInit` and persistent volume. (`legacyCompat` only) | `model-store` |
| `model.modelStorePath` | (deprecated) Specify location of unpacked model.                                                                                                        | `""`          |

### Storage parameters

| Name                                                              | Description                                                                                                                                                                                                                                   | Value                    |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `persistence`                                                     | Specify settings to modify the path `/model-store` if `model.legacyCompat` is enabled else `/.cache` volume where the model is served from.                                                                                                   |                          |
| `persistence.enabled`                                             | Enables the use of persistent volumes.                                                                                                                                                                                                        | `false`                  |
| `persistence.existingClaim`                                       | Specifies an existing persistent volume claim. If using `existingClaim`, run only one replica or use a `ReadWriteMany` storage setup.                                                                                                         | `""`                     |
| `persistence.storageClass`                                        | Specifies the persistent volume storage class. If set to `"-"`, this disables dynamic provisioning. If left undefined or set to null, the cluster default storage provisioner is used.                                                        | `""`                     |
| `persistence.accessMode`                                          | Specify `accessMode`. If using an NFS or similar setup, you can use `ReadWriteMany`.                                                                                                                                                          | `ReadWriteOnce`          |
| `persistence.stsPersistentVolumeClaimRetentionPolicy.whenDeleted` | Specifies persistent volume claim retention policy when deleted. Only used with Stateful Set volume templates.                                                                                                                                | `Retain`                 |
| `persistence.stsPersistentVolumeClaimRetentionPolicy.whenScaled`  | Specifies persistent volume claim retention policy when scaled. Only used with Stateful Set volume templates.                                                                                                                                 | `Retain`                 |
| `persistence.size`                                                | Specifies the size of the persistent volume claim (for example 40Gi).                                                                                                                                                                         | `50Gi`                   |
| `persistence.annotations`                                         | Adds annotations to the persistent volume claim.                                                                                                                                                                                              | `{}`                     |
| `hostPath`                                                        | Configures model cache on local disk on the nodes using `hostPath` -- for special cases. You should understand the security implications before using this option.                                                                            |                          |
| `hostPath.enabled`                                                | Enable `hostPath`.                                                                                                                                                                                                                            | `false`                  |
| `hostPath.path`                                                   | Specifies path on the node used as a `hostPath` volume.                                                                                                                                                                                       | `/model-store`           |
| `nfs`                                                             | Configures the model cache to sit on shared direct-mounted NFS. NOTE: you cannot set mount options using direct NFS mount to pods without a node-intalled nfsmount.conf. An NFS-based `PersistentVolumeClaim` is likely better in most cases. |                          |
| `nfs.enabled`                                                     | Enables direct pod NFS mount.                                                                                                                                                                                                                 | `false`                  |
| `nfs.path`                                                        | Specify path on NFS server to mount.                                                                                                                                                                                                          | `/exports`               |
| `nfs.server`                                                      | Specify NFS server address.                                                                                                                                                                                                                   | `nfs-server.example.com` |
| `nfs.readOnly`                                                    | Set to true to mount as read-only.                                                                                                                                                                                                            | `false`                  |

### Service parameters

| Name                  | Description                                            | Value       |
| --------------------- | ------------------------------------------------------ | ----------- |
| `service.type`        | Specifies the service type for the deployment.         | `ClusterIP` |
| `service.name`        | Overrides the default service name                     | `""`        |
| `service.openaiPort`  | Specifies Open AI Port for the service.                | `8000`      |
| `service.annotations` | Specify additional annotations to be added to service. | `{}`        |
| `service.labels`      | Specifies additional labels to be added to service.    | `{}`        |

### Multi-node parameters

Large models that must span multiple nodes do not work on plain Kubernetes with the GPU Operator alone at this time.
Optimized TensorRT profiles, when selected automatically or by environment variable, require either
[LeaderWorkerSets](https://github.com/kubernetes-sigs/lws) or the [MPI Operator]](https://github.com/kubeflow/mpi-operator)'s `MPIJobs` to be installed.
Since `MPIJob` is a batch-type resource that is not designed with service stability and reliability in mind, you should use LeaderWorkerSets if your cluster version allows it.
Only optimized profiles are supported for multi-node deployment at this time.

| Name                                 | Description                                                                                                                                                                     | Value   |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `multiNode.enabled`                  | Enables multi-node deployments.                                                                                                                                                 | `false` |
| `multiNode.clusterStartTimeout`      | Sets the number of seconds to wait for worker nodes to come up before failing.                                                                                                  | `300`   |
| `multiNode.gpusPerNode`              | Number of GPUs that will be presented to each pod. In most cases, this should match `resources.limits.nvidia.com/gpu`.                                                          | `1`     |
| `multiNode.workers`                  | Specifies how many worker pods per multi-node replica to launch.                                                                                                                | `1`     |
| `multiNode.leaderWorkerSet.enabled`  | NVIDIA recommends you use `LeaderWorkerSets` to deploy. If disabled, defaults to using `MPIJob` from mpi-operator.                                                              | `true`  |
| `multiNode.existingSSHSecret`        | Sets the SSH private key for MPI to an existing secret. Otherwise, the Helm chart generates a key randomly during installation.                                                 | `""`    |
| `multiNode.mpiJob.workerAnnotations` | Annotations only applied to workers for `MPIJob`, if used. This may be necessary to ensure the workers connect to `CNI`s offered by `multus` and the network operator, if used. | `{}`    |
| `multiNode.mpiJob.launcherResources` | Resources section to apply only to the launcher pods in `MPIJob`, if used. Launchers do not get the chart resources restrictions. Only workers do, since they require GPUs.     | `{}`    |
| `multiNode.optimized.enabled`        | Enables optimized multi-node deployments (currently the only option supported).                                                                                                 | `true`  |

