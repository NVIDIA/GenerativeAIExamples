{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
nim.common.v1.PVCTemplate decides if PVCs are created for statefulset templates
*/}}
{{- define "nim.common.v1.PVCTemplate" -}}
{{ ternary "1" "" (and (.Values.persistence.enabled | default false) (and ( .Values.statefulSet | default false) (.Values.statefulSet.enabled | default false)) (not .Values.persistence.existingClaim) (and (ne .Values.persistence.accessMode "ReadWriteMany") (ne .Values.persistence.accessMode "ReadOnlyMany"))) }}
{{- end -}}

{{/*
nim.common.v1.volumeMounts Defines volume mounts
*/}}
{{- define "nim.common.v1.volumeMounts" -}}
{{- if (include "nim.common.v1.nimCache" .) }}
- name: model-store
  mountPath: {{ include "nim.common.v1.nimCache" . }}
{{- end }}
{{if (include "nim.common.v1.nimCacheSubPath" .)}}
  subPath: {{ include "nim.common.v1.nimCacheSubPath" . }}
{{- end }}
- mountPath: /dev/shm
  name: dshm
{{- if .Values.extraVolumeMounts }}
{{- range $k, $v := .Values.extraVolumeMounts }}
- name: {{ $k }}
  {{- toYaml $v | nindent 2 }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
nim.common.v1.PVC defines the actual PVC for a NIM that isn't using StatefulSet templates
*/}}
{{- define "nim.common.v1.PVC" -}}
{{- if and .Values.persistence.enabled (not (include "nim.common.v1.PVCTemplate" .)) (not .Values.persistence.existingClaim )}}
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: {{ include "nim.common.v1.fullname" . }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
  {{- with .Values.persistence.annotations  }}
  annotations:
    {{ toYaml . | indent 4 }}
  {{- end }}
spec:
  accessModes:
    - {{ .Values.persistence.accessMode | quote }}
  resources:
    requests:
      storage: {{ .Values.persistence.size | quote }}
{{- if .Values.persistence.storageClass }}
  storageClassName: "{{ .Values.persistence.storageClass }}"
{{- end }}
{{ end }}
{{- end -}}
