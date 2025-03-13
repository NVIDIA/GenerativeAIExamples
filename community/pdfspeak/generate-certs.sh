#!/bin/bash
mkdir -p .certs
cd .certs
openssl req -x509 -newkey rsa:2048 -nodes -keyout localhost.key \
    -out localhost.crt -days 365 -subj "/CN=localhost"
cd ..
cp -r .certs /web-certs
cp -r .certs /backend-certs
rm -rf .certs
