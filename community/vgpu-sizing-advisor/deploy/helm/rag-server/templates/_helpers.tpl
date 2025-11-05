{{/*
Generate DockerConfigJson for image pull secrets
*/}}
{{- define "imagePullSecret" }}
{{- printf "{\"auths\":{\"%s\":{\"auth\":\"%s\"}}}" .Values.imagePullSecret.registry (printf "%s:%s" .Values.imagePullSecret.username .Values.imagePullSecret.password | b64enc) | b64enc }}
{{- end }}

{{/*
Create secret to access NGC Api
*/}}
{{- define "ngcApiSecret" }}
{{- printf "%s" .Values.ngcApiSecret.password | b64enc }}
{{- end }}
