import json

import requests

import kube_notify
import kube_notify.logger as logger


def check_selector(
    resource_name, resources, resource_type, labels, involved_object_kind
):
    for resource in resources:
        if resource["name"] == resource_name:
            if "selector" in resource:
                selectors = resource.get("selector", {})
                return (
                    resource_type in selectors.get("types", [resource_type])
                    and (
                        selectors.get("labels") is None
                        or any(
                            (
                                label.get("key"),
                                label.get("value", labels.get(label.get("key"))),
                            )
                            in labels.items()
                            for label in selectors.get("labels", [])
                        )
                    )
                    and (
                        selectors.get("involvedObjectKind") is None
                        or involved_object_kind in selectors.get("involvedObjectKind")
                    )
                )
            elif "excludeSelector" in resource:
                selectors = resource.get("excludeSelector", {})
                return not (
                    resource_type in selectors.get("types", [])
                    or any(
                        (
                            label.get("key"),
                            label.get("value", labels.get(label.get("key"))),
                        )
                        in labels.items()
                        for label in selectors.get("labels", [])
                    )
                    or involved_object_kind in selectors.get("involvedObjectKind", [])
                )
            return True
    return False


async def handle_notify(
    resource_name,
    title,
    description,
    fields,
    event_info,
    kube_notify_config,
    resource_type,
    labels,
    involved_object_kind=None,
):
    notifs = ["Skipping"]
    if event_info[0].timestamp() > kube_notify.STARTUP_TIME.timestamp():
        # Send notification
        notifs = ["Excluded"]
        for group_name, group in kube_notify_config.get("notifications", {}).items():
            if check_selector(
                resource_name,
                group.get("resources"),
                resource_type,
                labels,
                involved_object_kind,
            ):
                notifs = []
                if group.get("discord"):
                    notifs.append(f"{group_name}/discord")
                    discord = group.get("discord")
                    send_discord_webhook(
                        discord["webhook"],
                        title,
                        description,
                        fields,
                        discord.get("username"),
                        discord.get("avatar_url"),
                    )
                if group.get("gotify"):
                    gotify = group.get("gotify")
                    notifs.append(f"{group_name}/gotify")
                    send_gotify_message(
                        gotify["url"], gotify["token"], title, description, fields
                    )
    logger.logger.info(f"{event_info[0]} [{','.join(notifs)}] {description}")


def send_gotify_message(url, token, title, description, fields):
    # Construct the HTTP request for sending a message to Gotify
    url = f"{url}/message?token={token}&format=markdown"
    headers = {"Content-Type": "application/json"}
    message = f"**{description}**\n\n"
    message += "| Clé | Valeur |\n"
    message += "| ---- | ---- |\n"
    for key, value in fields.items():
        message += f"| {key} | {value} |\n"
    data = {
        "title": title,
        "message": message,
        "extras": {"client::display": {"contentType": "text/markdown"}},
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        logger.logger.error("Failed to send notification to Gotify")


def send_discord_webhook(
    webhook_url, title, description, fields, username="kube-notify", avatar_url=None
):
    # Construct the HTTP request for sending a message to Discord via the Webhook
    headers = {"Content-Type": "application/json"}

    data = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "fields": [
                    {"name": key, "value": value, "inline": True}
                    for key, value in fields.items()
                ],
            }
        ]
    }
    # Optionally add username and avatar_url to customize the webhook message sender
    if username:
        data["username"] = username
    if avatar_url:
        data["avatar_url"] = avatar_url
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    if response.status_code != 204:
        logger.logger.error("Failed to send notification to Discord")
