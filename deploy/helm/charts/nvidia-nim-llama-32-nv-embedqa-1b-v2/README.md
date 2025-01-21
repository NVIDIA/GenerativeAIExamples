## NVIDIA Retrieval QA Llama 3.2 1B Text Embedding NIM v2

### Setup Environment

First create your namespace and your secrets

```bash

NAMESPACE=nvidia-nims
DOCKER_CONFIG='{"auths":{"nvcr.io":{"username":"$oauthtoken", "password":"'${NGC_API_KEY}'" }}}'
echo -n $DOCKER_CONFIG | base64 -w0
NGC_REGISTRY_PASSWORD=$(echo -n $DOCKER_CONFIG | base64 -w0 )

kubectl create namespace ${NAMESPACE}
kubectl apply -n ${NAMESPACE} -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: ngc-secret
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: ${NGC_REGISTRY_PASSWORD}
EOF
kubectl create -n ${NAMESPACE} secret generic ngc-api --from-literal=NGC_API_KEY=${NGC_API_KEY}

```

Install the chart

```bash
helm upgrade \
    --install \
    --username '$oauthtoken' \
    --password "${NGC_API_KEY}" \
    -n ${NAMESPACE} \
    --set persistence.class="local-nfs" \
    llama-32-nv-embedqa-1b-v2 \
    .
```

#### Set the Container Image

Add the following to update the container image for the helm chart:

```bash
--set image.repository="nvcr.io/nim/nvidia/llama-3.2-nv-embedqa-1b-v2" \
--set image.tag="1.3.0" \
```

### Parameters

#### Deployment parameters

| Name                              | Description                                                                                                                                                                                 | Value   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `affinity`                        | [default: {}] Affinity settings for deployment.                                                                                                                                             | `{}`    |
| `containerSecurityContext`        | Sets privilege and access control settings for container (Only affects the main container, not pod-level)                                                                                   | `{}`    |
| `customCommand`                   | Overrides command line options sent to the NIM with the array listed here.                                                                                                                  | `[]`    |
| `customArgs`                      | Overrides command line arguments of the NIM container with the array listed here.                                                                                                           | `[]`    |
| `egress_endpoint`                |  Specifies the egress endpoints for the service which are added as an env var with prefix 'egress_'                                                                                                 | `{}`    |
| `envVars`                         | Adds arbitrary environment variables to the main container using key-value pairs, for example NAME: value                                                                                   | `{}`    |
| `extraVolumes`                    | Adds arbitrary additional volumes to the deployment set definition                                                                                                                          | `{}`    |
| `extraVolumeMounts`               | Specify volume mounts to the main container from `extraVolumes`                                                                                                                             | `{}`    |
| `image.repository`                | NIM Image Repository                                                                                                                                                                    | `""`    |
| `image.tag`                       | Image tag or version                                                                                                                                                                        | `""`    |
| `image.pullPolicy`                | Image pull policy                                                                                                                                                                           | `""`    |
| `imagePullSecrets`                | Specify list of secret names that are needed for the main container and any init containers.                                                                                                |         |
| `ingress_endpoint`                | Specifies the ingress endpoints for the service which are added as an env var with prefix 'ingress_'                                                                                                 | `{}`    |
| `initContainers`                  | Specify init containers, if needed.`initContainers` are defined as an object with the name of the container as the key. All other elements of the `initContainer` definition are the value. | `{}`    |
| `nodeSelector`                    | Sets node selectors for the NIM -- for example `nvidia.com/gpu.present: "true"`                                                                                                             | `{}`    |
| `params`                          | Specifies the params mentioned in a separate config file inside nim-workspace dir which will be added as env var.                                                                                                 | `{}`    |
| `podAnnotations`                  | Sets additional annotations on the main deployment pods                                                                                                                                     | `{}`    |
| `podSecurityContext`              | Specify privilege and access control settings for pod                                                                                                                                       |         |
| `podSecurityContext.runAsUser`    | Specify user UID for pod.                                                                                                                                                                   | `1000`  |
| `podSecurityContext.runAsGroup`   | Specify group ID for pod.                                                                                                                                                                   | `1000`  |
| `podSecurityContext.fsGroup`      | Specify file system owner group id.                                                                                                                                                         | `1000`  |
| `replicaCount`                    | Specify static replica count for deployment.                                                                                                                                                | `1`     |
| `resources`                       | Specify resources limits and requests for the running service.                                                                                                                              |         |
| `resources.limits.nvidia.com/gpu` | Specify number of GPUs to present to the running service.                                                                                                                                   | `1`     |
| `serviceAccount.create`           | Specifies whether a service account should be created.                                                                                                                                      | `false` |
| `serviceAccount.annotations`      | Sets annotations to be added to the service account.                                                                                                                                        | `{}`    |
| `serviceAccount.name`             | Specifies the name of the service account to use. If it is not set and create is `true`, a name is generated using a `fullname` template.                                                   | `""`    |
| `statefulSet.enabled`             | Enables `statefulset` deployment. Enabling `statefulSet` allows PVC templates for scaling. If using central PVC with RWX `accessMode`, this isn't needed.                                   | `false` |
| `tolerations`                     | Specify tolerations for pod assignment. Allows the scheduler to schedule pods with matching taints.                                                                                         |         |

#### Autoscaling parameters

Values used for creating a `Horizontal Pod Autoscaler`. If autoscaling is not enabled, the rest are ignored.
NVIDIA recommends usage of the custom metrics API, commonly implemented with the prometheus-adapter.
Standard metrics of CPU and memory are of limited use in scaling NIM.

| Name                      | Description                               | Value   |
| ------------------------- | ----------------------------------------- | ------- |
| `autoscaling.enabled`     | Enables horizontal pod autoscaler.        | `false` |
| `autoscaling.minReplicas` | Specify minimum replicas for autoscaling. | `1`     |
| `autoscaling.maxReplicas` | Specify maximum replicas for autoscaling. | `10`    |
| `autoscaling.metrics`     | Array of metrics for autoscaling.         | `[]`    |

#### Ingress parameters

| Name                                 | Description                                           | Value                    |
| ------------------------------------ | ----------------------------------------------------- | ------------------------ |
| `ingress.enabled`                    | Enables ingress.                                      | `false`                  |
| `ingress.className`                  | Specify class name for Ingress.                       | `""`                     |
| `ingress.annotations`                | Specify additional annotations for ingress.           | `{}`                     |
| `ingress.hosts`                      | Specify list of hosts each containing lists of paths. |                          |
| `ingress.hosts[0].host`              | Specify name of host.                                 | `chart-example.local`    |
| `ingress.hosts[0].paths[0].path`     | Specify ingress path.                                 | `/`                      |
| `ingress.hosts[0].paths[0].pathType` | Specify path type.                                    | `ImplementationSpecific` |
| `ingress.tls`                        | Specify list of pairs of TLS `secretName` and hosts.  | `[]`                     |

#### Probe parameters

| Name                                 | Description                                | Value              |
| ------------------------------------ | ------------------------------------------ | ------------------ |
| `livenessProbe.enabled`              | Enables `livenessProbe``                   | `true`             |
| `livenessProbe.path`                 | `LivenessProbe`` endpoint path             | `/v1/health/live`  |
| `livenessProbe.initialDelaySeconds`  | Initial delay seconds for `livenessProbe`  | `15`               |
| `livenessProbe.timeoutSeconds`       | Timeout seconds for `livenessProbe`        | `1`                |
| `livenessProbe.periodSeconds`        | Period seconds for `livenessProbe`         | `10`               |
| `livenessProbe.successThreshold`     | Success threshold for `livenessProbe`      | `1`                |
| `livenessProbe.failureThreshold`     | Failure threshold for `livenessProbe`      | `3`                |
| `readinessProbe.enabled`             | Enables `readinessProbe`                   | `true`             |
| `readinessProbe.path`                | Readiness Endpoint Path                    | `/v1/health/ready` |
| `readinessProbe.initialDelaySeconds` | Initial delay seconds for `readinessProbe` | `15`               |
| `readinessProbe.timeoutSeconds`      | Timeout seconds for `readinessProbe`       | `1`                |
| `readinessProbe.periodSeconds`       | Period seconds for `readinessProbe`        | `10`               |
| `readinessProbe.successThreshold`    | Success threshold for `readinessProbe`     | `1`                |
| `readinessProbe.failureThreshold`    | Failure threshold for `readinessProbe`     | `3`                |
| `startupProbe.enabled`               | Enables `startupProbe`                     | `true`             |
| `startupProbe.path`                  | `StartupProbe` Endpoint Path               | `/v1/health/ready` |
| `startupProbe.initialDelaySeconds`   | Initial delay seconds for `startupProbe`   | `40`               |
| `startupProbe.timeoutSeconds`        | Timeout seconds for `startupProbe`         | `1`                |
| `startupProbe.periodSeconds`         | Period seconds for `startupProbe`          | `10`               |
| `startupProbe.successThreshold`      | Success threshold for `startupProbe`       | `1`                |
| `startupProbe.failureThreshold`      | Failure threshold for `startupProbe`       | `180`              |

#### Metrics parameters

| Name                                      | Description                                                                                 | Value   |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- | ------- |
| `metrics.port`                            | For NIMs with a separate metrics port, this opens that port on the container                | `0`     |
| `serviceMonitor`                          | Options for `serviceMonitor` to use the Prometheus Operator and the primary service object. |         |
| `metrics.serviceMonitor.enabled`          | Enables `serviceMonitor` creation.                                                          | `false` |
| `metrics.serviceMonitor.additionalLabels` | Specify additional labels for ServiceMonitor.                                               | `{}`    |

#### NIM parameters

| Name               | Description                                                                                                 | Value  |
| ------------------ | ----------------------------------------------------------------------------------------------------------- | ------ |
| `nim.nimCache`     | Path to mount writeable storage or pre-filled model cache for the NIM                                       | `""`   |
| `nim.modelName`    | Optionally specifies the name of the model in the API. This can be used in helm tests.                      | `""`   |
| `nim.ngcAPISecret` | Name of pre-existing secret with a key named `NGC_API_KEY` that contains an API key for NGC model downloads | `""`   |
| `nim.ngcAPIKey`    | NGC API key literal to use as the API secret and image pull secret when set                                 | `""`   |
| `nim.serverPort`   | Specify Server Port.                                                                                        | `0`    |
| `nim.httpPort`     | Specify HTTP Port.                                                                                          | `8000` |
| `nim.grpcPort`     | Specify GRPC Port.                                                                                          | `0`    |
| `nim.labels`       | Specify extra labels to be add to on deployed pods.                                                         | `{}`   |
| `nim.jsonLogging`  | Whether to enable JSON lines logging. Defaults to true.                                                     | `true` |
| `nim.logLevel`     | Log level of NIM service. Possible values of the variable are TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL. | `INFO` |

#### Storage parameters

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
| `nfs.enabled`                                                     | Enable direct pod NFS mount                                                                                                                                                                                                                   | `false`                  |
| `nfs.path`                                                        | Specify path on NFS server to mount                                                                                                                                                                                                           | `/exports`               |
| `nfs.server`                                                      | Specify NFS server address                                                                                                                                                                                                                    | `nfs-server.example.com` |
| `nfs.readOnly`                                                    | Set to true to mount as read-only                                                                                                                                                                                                             | `false`                  |

#### Service parameters

| Name                  | Description                                                                                  | Value       |
| --------------------- | -------------------------------------------------------------------------------------------- | ----------- |
| `service.type`        | Specifies the service type for the deployment.                                               | `ClusterIP` |
| `service.name`        | Overrides the default service name                                                           | `""`        |
| `service.serverPort`  | Specifies the Server Port for the service.                                                   | `0`         |
| `service.httpPort`    | Specifies the HTTP Port for the service.                                                     | `8000`      |
| `service.grpcPort`    | Specifies the GRPC Port for the service.                                                     | `0`         |
| `service.metricsPort` | Specifies the metrics port on the main service object. Some NIMs do not use a separate port. | `0`         |
| `service.annotations` | Specify additional annotations to be added to service.                                       | `{}`        |
| `service.labels`      | Specifies additional labels to be added to service.                                          | `{}`        |
