{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{- define "nim.common.v1.hpa" -}}
---
{{ if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "nim.common.v1.fullname" . }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
spec:
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  scaleTargetRef:
    {{- if (and .Values.multinode (and .Values.multiNode.enabled | default false (or (.Capabilities.APIVersions.Has "leaderworkerset.x-k8s.io/v1") .Values.multiNode.leaderWorkerSet.enabled))) }}
    apiVersion: leaderworkerset.x-k8s.io/v1
    kind: LeaderWorkerSet
    {{- else if (and .Values.statefulSet (.Values.statefulSet.enabled | default false)) }}
    apiVersion: apps/v1
    kind: StatefulSet
    {{- else }}
    apiVersion: apps/v1
    kind: Deployment
    {{- end }}
    name: {{ include "nim.common.v1.fullname" . }}
  metrics:
    {{- range .Values.autoscaling.metrics }}
        - {{- . | toYaml | nindent 10 }}
    {{- end }}
  {{- if .Values.autoscaling.scaleDownStabilizationSecs }}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: {{ .Values.autoscaling.scaleDownStabilizationSecs }}
  {{- end }}
{{ end }}

{{- end -}}
