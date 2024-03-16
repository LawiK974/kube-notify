# Kube Gotify

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
  - [ ] Latest release
  - [ ] CI passing
  - [ ] License
  - [ ] Coverage
- [ ] Add OpenAI module to send recomendation messages for non-normal events.
- [ ] Documenting
  - [x] Installation
  - [ ] Configuration
- [ ] Notification services
  - [x] Discord
  - [x] Gotify
  - [ ] Mattermost
  - [ ] Slack
  - [ ] Telegram
- [ ] Automation (GitHub Actions)
  - [ ] Coverage tests
  - [x] pre-commit
  - [x] Docker build & push (latest + releases)

## References

- [kubernetes_asyncio](https://github.com/tomplus/kubernetes_asyncio)
- [Link to the corresponding docker image](https://hub.docker.com/r/wikle/kube-notify)
