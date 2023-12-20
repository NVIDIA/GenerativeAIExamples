#!/bin/bash

# [~/helm-charts/nvidia]$ helm package kvm-driver-container-0.1.0
# Successfully packaged chart and saved it to: /home/zvonkok/helm-charts/nvidia/kvm-driver-container-0.1.0.tgz
# [~/helm-charts/nvidia]$ helm repo index . --url=file:///$PWD

FILE=${4/file:\/\//}

echo $FILE >> /tmp/log.txt

cat $FILE
