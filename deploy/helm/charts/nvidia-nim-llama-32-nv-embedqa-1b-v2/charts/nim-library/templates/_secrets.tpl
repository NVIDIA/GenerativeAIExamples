{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
For inline NGC key, create image pull secret
*/}}
{{- define "nim.common.v1.generatedImagePullSecret" -}}
{{- if (include "nim.common.v1.ngcAPIKey" .) }}
{{- printf "{\"auths\":{\"nvcr.io\":{\"username\":\"$oauthtoken\",\"password\":\"%s\"}}}" (include "nim.common.v1.ngcAPIKey" .) | b64enc }}
{{- end }}
{{- end }}


{{/*
nim.common.v1.generatedSecrets For inline, literal NGC API key added for demos or managed values files
*/}}
{{- define "nim.common.v1.generatedSecrets" -}}
{{ if (include "nim.common.v1.ngcAPIKey" .) }}
---
apiVersion: v1
kind: Secret
metadata:
  name: {{ (first .Values.imagePullSecrets).name }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: {{ template "nim.common.v1.generatedImagePullSecret" . }}
---
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "nim.common.v1.ngcAPISecret" . }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
type: Opaque
data:
  NGC_API_KEY: {{ (include "nim.common.v1.ngcAPIKey" .) | b64enc }}
{{ end }}
{{- end -}}
