{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
nim.common.v1.service defines the service for the NIM
*/}}
{{- define "nim.common.v1.service" -}}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.service.name | default (include "nim.common.v1.fullname" .) }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
    {{- if .Values.service.labels }}
    {{- toYaml .Values.service.labels | nindent 4 }}
    {{- end }}
  annotations:
    {{- if .Values.service.annotations }}
    {{- toYaml .Values.service.annotations | nindent 4 }}
    {{- end }}
spec:
  type: {{ .Values.service.type }}
  ports:
    {{- if .Values.service.httpPort }}
    - port: {{ .Values.service.httpPort }}
      targetPort: http
      protocol: TCP
      name: http
    {{- end }}
    {{- if .Values.service.grpcPort }}
    - port: {{ .Values.service.grpcPort }}
      targetPort: grpc
      protocol: TCP
      name: grpc
    {{- end }}
    {{- if .Values.service.metricsPort }}
    - port: {{ .Values.service.metricsPort }}
      targetPort: metrics
      name: metrics
    {{- end }}
    {{- if .Values.service.serverPort }}
    - port: {{ .Values.service.serverPort }}
      targetPort: http-server
      name: http-server
    {{- end }}
  selector:
    {{- include "nim.common.v1.selectorLabels" . | nindent 4 }}
    {{- include "nim.common.v1.nimLabels" . | nindent 4 }}
    {{- if (and .Values.multiNode (.Values.multiNode.enabled | default false)) }}
    {{- if (or (.Capabilities.APIVersions.Has "leaderworkerset.x-k8s.io/v1") .Values.multiNode.leaderWorkerSet.enabled) }}
    nim-llm-role: "leader"
    {{- else }}
    training.kubeflow.org/replica-index: "0"
    {{- end }}
    {{- end }}

{{- if (and .Values.statefulSet (.Values.statefulSet.enabled | default false)) }}
{{- if (not (and .Values.multiNode (.Values.multiNode.enabled | default false))) }}
---
{{/*
If using statefulSet, ensure a headless service also exists to satisfy the API correctly
*/}}
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.service.name | default (include "nim.common.v1.fullname" .) }}-sts
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
    {{- if .Values.service.labels }}
    {{- toYaml .Values.service.labels | nindent 4 }}
    {{- end }}
  annotations:
    {{- if .Values.service.annotations }}
    {{- toYaml .Values.service.annotations | nindent 4 }}
    {{- end }}
spec:
  type: ClusterIP
  clusterIP: None
  ports:
    {{- if .Values.service.httpPort }}
    - port: {{ .Values.service.httpPort }}
      targetPort: http
      protocol: TCP
      name: http
    {{- end }}
    {{- if .Values.service.grpcPort }}
    - port: {{ .Values.service.grpcPort }}
      targetPort: grpc
      protocol: TCP
      name: grpc
    {{- end }}
    {{/*
    If using a serviceMonitor on the primary service with a separate metrics port, this is required.
    Don't do this on a public endpoint via LoadBalancer service.
    */}}
    {{- if .Values.service.metricsPort }}
    - port: {{ .Values.service.metricsPort }}
      targetPort: metrics
      name: metrics
    {{- end }}
    {{- if .Values.service.serverPort }}
    - port: {{ .Values.service.serverPort }}
      targetPort: http-server
      name: http-server
    {{- end }}
  selector:
    {{- include "nim.common.v1.selectorLabels" . | nindent 4 }}
    {{- include "nim.common.v1.nimLabels" . | nindent 4 }}
{{- end }}
{{- end }}
{{- end -}}
