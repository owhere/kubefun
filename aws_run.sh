#! /bin/bash

# docker built -t kubefun .

docker run -d -p 39027:5000 \
  -e AWS_PROFILE=default \
  -e AWS_SSO_SESSION=apps-k8s-dev \
  -v ~/.aws:/root/.aws\
  -v ~/.kube/config:/root/.kube/config:ro \
  kubefun
