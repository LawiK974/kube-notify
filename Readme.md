# Kube Gotify

An app that watches kubernetes resource creation, deletion, updates and errors events and notify selected events to gotify.

## Installation

`Kube-notify`

1. Create and modify configuration file :

```sh
cp config.sample.yaml config.yaml
vim config.yaml
kubectl create cm kube-notify-config -n monitoring --from-file config.yaml
```

2. Deploy resources (deployement + rbac) in `monitoring` namespace :

```sh
kubectl apply -n monitoring -f deployement.yaml
```

## Configuration

All configuration are in `/app/config.yaml` file.
Use [sample config](./config.sample.yaml) as an example.

## References

- [kubernetes_asyncio](https://github.com/tomplus/kubernetes_asyncio)
