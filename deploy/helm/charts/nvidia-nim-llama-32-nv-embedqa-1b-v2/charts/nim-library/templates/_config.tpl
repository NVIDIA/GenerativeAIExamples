{{/*
Copyright NVIDIA, Inc. All Rights Reserved.
SPDX-License-Identifier: APACHE-2.0
*/}}

{{/*
nim.common.v1.nimCache specifies the path to the model cache
*/}}
{{- define "nim.common.v1.nimCache" -}}
{{- if .Values.model -}}
{{ .Values.model.nimCache | default "" }}
{{- else if .Values.nim -}}
{{ .Values.nim.nimCache | default "" }}
{{- else -}}
""
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.nimCacheSubPath specifies a subDir to mount for the model cache path to be accurate
*/}}
{{- define "nim.common.v1.nimCacheSubPath" -}}
{{- if .Values.model -}}
{{ .Values.model.nimCacheSubPath | default "" }}
{{- else if .Values.nim -}}
{{ .Values.nim.nimCacheSubPath | default "" }}
{{- else -}}
""
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.ngcAPISecret specifies the path to the model cache
*/}}
{{- define "nim.common.v1.ngcAPISecret" -}}
{{- if .Values.model -}}
{{ .Values.model.ngcAPISecret | default "" }}
{{- else if .Values.nim -}}
{{ .Values.nim.ngcAPISecret | default "" }}
{{- else -}}
""
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.ngcAPIEnvName specifies the environment variable name that the container expects for NGC CLI/SDK
*/}}
{{- define "nim.common.v1.ngcAPIEnvName" -}}
{{- if .Values.model -}}
{{ .Values.model.ngcAPIEnvName | default "NGC_API_KEY" }}
{{- else if .Values.nim -}}
{{ .Values.nim.ngcAPIEnvName | default "NGC_API_KEY" }}
{{- else -}}
""
{{- end -}}
{{- end -}}


{{/*
nim.common.v1.env generates an env var array out of a dict or array of supported values
*/}}

{{- define "nim.common.v1.env" -}}
{{- if .Values.env -}}
{{- toYaml .Values.env -}}
{{- else -}}
{{- range $k, $v := .Values.envVars }}
- name: {{ $k }}
  value: {{ $v | quote }}
{{- range $k, $v := .Values.ingress_endpoint }}
- name: ingress_{{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- range $k, $v := .Values.egress_endpoint}}
- name: egress_{{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- range $k, $v := .Values.params }}
- name: {{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- end }}
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.jsonLogging specifies the path to the model cache
*/}}
{{- define "nim.common.v1.jsonLogging" -}}
{{- if .Values.model -}}
{{- if .Values.model.jsonLogging -}}
1
{{- else -}}
0
{{- end -}}
{{- else if .Values.nim -}}
{{- if .Values.nim.jsonLogging -}}
1
{{- else -}}
0
{{- end -}}
{{- else -}}
0
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.logLevel sets a log level environment variable
*/}}
{{- define "nim.common.v1.logLevel" -}}
{{- if .Values.model -}}
{{ .Values.model.logLevel | default "INFO" }}
{{- else if .Values.nim -}}
{{ .Values.nim.logLevel | default "INFO" }}
{{- else -}}
"INFO"
{{- end -}}
{{- end -}}

{{/*
nim.common.v1.ngcAPIKey allows an actual secret used on CLI or in securely stored file
*/}}
{{- define "nim.common.v1.ngcAPIKey" -}}
{{- if .Values.model -}}
{{ .Values.model.ngcAPIKey | default "" }}
{{- else if .Values.nim -}}
{{ .Values.nim.ngcAPIKey | default "" }}
{{- else -}}
""
{{- end -}}
{{- end -}}
