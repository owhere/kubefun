# AWS EKS Deployment

- Dev Deployment

```bash
kubectl apply -k overlays/dev
```


- Secret needed for k8s deployment

```bash
kubectl create secret generic kubefun-aws-env \
    --from-literal=AWS_PROFILE=default \
    --from-literal=AWS_SSO_SESSION=apps-k8s-dev \
    -n kubefun
```