{{/*
Create secret to access docker registry
*/}}
{{- define "imagePullSecret" }}
{{- printf "{\"auths\": {\"%s\": {\"auth\": \"%s\"}}}" .Values.images.registry.name (printf "%s:%s" .Values.images.registry.imagePullSecret.username .Values.images.registry.imagePullSecret.password | b64enc) | b64enc }}
{{- end }}

{{/*
Full image name with tag
*/}}
{{- define "developer-llm-operator.fullimage" -}}
{{- if .Values.images.version }}
{{- .Values.images.name -}}:{{- .Values.images.version -}}
{{- else }}
{{- .Values.images.name -}}:v{{- .Chart.AppVersion -}}
{{- end }}
{{- end }}
