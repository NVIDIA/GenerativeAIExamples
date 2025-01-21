{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
nim.common.v1.deployment creates a NIM deployment using an appropriate object
*/}}
{{- define "nim.common.v1.deployment" -}}
{{- $pvcUsingTemplate := (include "nim.common.v1.PVCTemplate" .) }}
---
apiVersion: apps/v1
{{- if (and .Values.statefulSet (.Values.statefulSet.enabled | default false)) }}
kind: StatefulSet
{{- else }}
kind: Deployment
{{- end }}
metadata:
  name: {{ include "nim.common.v1.fullname" . }}
  labels:
    {{- include "nim.common.v1.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "nim.common.v1.selectorLabels" . | nindent 6 }}
      {{- if (include "nim.common.v1.nimLabels" . ) }}
      {{- include "nim.common.v1.nimLabels" . | nindent 6 }}
      {{- end }}
  {{- if (and .Values.statefulSet (.Values.statefulSet.enabled | default false)) }}
  serviceName: {{ .Values.service.name | default (include "nim.common.v1.fullname" .) }}-sts
  podManagementPolicy: "Parallel"
  {{- else }}
  progressDeadlineSeconds: 3600
  {{- end }}
  template:
    metadata:
      {{- with ( include "nim.common.v1.nimAnnotations" . ) }}
      annotations:
        {{- . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "nim.common.v1.selectorLabels" . | nindent 8 }}
        {{- include "nim.common.v1.nimLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "nim.common.v1.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      initContainers:
      {{- range $k, $v := .Values.initContainers }}
        - name: {{ $k }}
          {{- toYaml $v | nindent 10 }}
      {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.containerSecurityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- if or .Values.customCommand }}
          command:
            {{- if .Values.customCommand }}
            {{- range .Values.customCommand }}
             - {{ . | quote }}
            {{- end }}
            {{- end }}
          {{- end }}
          {{- if .Values.customArgs }}
          args:
            {{- if .Values.customArgs }}
            {{- range .Values.customArgs }}
             - {{ . | quote }}
            {{- end }}
            {{- end }}
          {{- end }}
          env:
            {{- if (include "nim.common.v1.nimCache" .) }}
            - name: NIM_CACHE_PATH
              value: {{ include "nim.common.v1.nimCache" . | quote }}
            {{- end }}
            {{- if (include "nim.common.v1.ngcAPISecret" .) }}
            - name: {{ include "nim.common.v1.ngcAPIEnvName" . }}
              valueFrom:
                secretKeyRef:
                  name: {{ include "nim.common.v1.ngcAPISecret" . }}
                  key: NGC_API_KEY
            {{- end }}
            - name: NIM_SERVER_PORT
              value: {{ include "nim.common.v1.nimServerPort" . | quote }}
            - name: NIM_JSONL_LOGGING
              value: {{ include "nim.common.v1.jsonLogging" . | quote }}
            - name: NIM_LOG_LEVEL
              value: {{ include "nim.common.v1.logLevel" . | quote }}
            {{- if (include "nim.common.v1.env" .) }}
            {{- include "nim.common.v1.env" . | nindent 12 }}
            {{- end }}
          ports:
            {{- include "nim.common.v1.ports" . | nindent 12 }}
          {{- include "nim.common.v1.probes" . | indent 10 }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            {{- include "nim.common.v1.volumeMounts" . | nindent 12 }}
      terminationGracePeriodSeconds: 60
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      volumes:
        - name: dshm
          emptyDir:
            medium: Memory
            {{- if .Values.shmSize }}
            size: {{ .Values.shmSize }}
            {{- end }}
        {{- if (and (not (include "nim.common.v1.PVCTemplate" .)) (include "nim.common.v1.nimCache" .))}}
        - name: model-store
          {{- if .Values.persistence.enabled }}
          persistentVolumeClaim:
            claimName:  {{ .Values.persistence.existingClaim | default (include "nim.common.v1.fullname" .) }}
          {{- else if .Values.hostPath.enabled }}
          hostPath:
            path: {{ .Values.hostPath.path }}
            type: DirectoryOrCreate
          {{- else if .Values.nfs.enabled }}
          nfs:
            server: {{ .Values.nfs.server | quote }}
            path: {{ .Values.nfs.path }}
            readOnly: {{ .Values.nfs.readOnly }}
          {{- else }}
          emptyDir: {}
          {{- end }}
        {{- end }}
      {{- if .Values.extraVolumes }}
      {{- range $k, $v := .Values.extraVolumes }}
        - name: {{ $k }}
          {{- toYaml $v | nindent 10 }}
      {{- end }}
      {{- end }}
  {{- if (and (include "nim.common.v1.PVCTemplate" .) (include "nim.common.v1.nimCache" .))}}
  {{- with .Values.persistence.stsPersistentVolumeClaimRetentionPolicy }}
  persistentVolumeClaimRetentionPolicy:
    whenDeleted: {{ .whenDeleted }}
    whenScaled: {{ .whenScaled }}
  {{- end }}
  volumeClaimTemplates:
  - metadata:
      name: model-store
      labels:
        {{- include "nim.common.v1.labels" . | nindent 8 }}
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
  {{- end }}
{{- end -}}
