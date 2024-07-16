# Kube Notify

![GitHub License](https://img.shields.io/github/license/LawiK974/kube-notify)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
![GitHub Release](https://img.shields.io/github/v/release/LawiK974/kube-notify?display_name=release&link=https%3A%2F%2Fgithub.com%2FLawiK974%2Fkube-notify%2Freleases%2Flatest)
![GitHub Actions Workflow Status Main](https://img.shields.io/github/actions/workflow/status/LawiK974/kube-notify/github-actions-docker.yml?branch=main&label=Build%26Push%20Main)
![GitHub Actions Workflow Status Release](https://img.shields.io/github/actions/workflow/status/LawiK974/kube-notify/github-actions-docker-tags.yml?label=Build%26Push%20Release)


An app that watches kubernetes resource creation, deletion, updates and errors events and notify selected events to gotify.

## Screenshots

| Gotify | Discord |
|--------|---------|
| ![](./images/gotify.jpg)  | ![](./images/discord.jpg) |

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
kubectl apply -f deployement.yaml
```

## Configuration

All configuration are in `/app/config.yaml` file.
Use [sample config](./config.sample.yaml) as an example.

## To do

- [ ] Optimize Code
- [ ] Badges
  - [x] Latest release
  - [x] CI passing
  - [x] License
  - [ ] Coverage
- Fonctionnalities
  - [x] Stream CoreAPI Events
  - [x] Possibility to stream Velero backups
  - [x] Filter notifications on the following criteria : types, reasons, labels, namespaces, involvedObjectKind
  - [ ] Track Pod termination reasons
  - [ ] Add OpenAI module to send recomendation messages for non-normal events.
- [ ] Create Helm chart
- [ ] Documenting
  - [x] Installation
  - [ ] Configuration
- [ ] Notification services
  - [x] Discord
  - [x] Gotify
  - [x] Mattermost
  - [ ] Slack
  - [ ] Telegram
- [ ] Automation (GitHub Actions)
  - [ ] Coverage tests
  - [x] pre-commit
  - [x] Trivy security scan
  - [x] Docker build & push (latest + releases)

## References

- [kubernetes_asyncio](https://github.com/tomplus/kubernetes_asyncio)
- [Link to the corresponding docker image](https://hub.docker.com/r/wikle/kube-notify)
