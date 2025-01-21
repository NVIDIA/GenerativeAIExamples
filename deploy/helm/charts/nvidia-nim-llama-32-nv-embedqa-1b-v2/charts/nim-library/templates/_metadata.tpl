{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "nim.common.v1.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "nim.common.v1.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nim.common.v1.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nim.common.v1.labels" -}}
helm.sh/chart: {{ include "nim.common.v1.chart" . }}
{{ include "nim.common.v1.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "nim.common.v1.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nim.common.v1.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "nim.common.v1.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "nim.common.v1.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
NIM pod-specific labels and annotations
*/}}
{{- define "nim.common.v1.nimLabels" -}}
{{- if .Values.podLabels }}
{{- toYaml .Values.podLabels }}
{{- else if .Values.model -}}
{{- if .Values.model.labels }}
{{- toYaml .Values.model.labels }}
{{- end }}
{{- else if .Values.nim -}}
{{- if .Values.nim.labels }}
{{- toYaml .Values.nim.labels }}
{{- end }}
{{- else }}
{}
{{- end -}}
{{- end -}}

{{- define "nim.common.v1.nimAnnotations" -}}
{{- if .Values.podAnnotations -}}
{{ toYaml .Values.podAnnotations }}
{{- else if .Values.nim -}}
{{- if .Values.nim.annotations -}}
{{ toYaml .Values.nim.annotations }}
{{- end -}}
{{- else -}}
{}
{{- end -}}
{{- end -}}
