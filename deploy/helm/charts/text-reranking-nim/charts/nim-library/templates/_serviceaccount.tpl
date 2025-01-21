{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
nim.common.v1.serviceAccount optionally creates a service account
*/}}
{{- define "nim.common.v1.serviceAccount" -}}
---
{{ if .Values.serviceAccount.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "nim.common.v1.serviceAccountName" . }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{ end }}
{{- end -}}
