import requests
import json
from kube_notify.logger import logger
from kube_notify import STARTUP_TIME


def check_selector(resource_name, resources, resource_type, labels):
    for resource in resources:
        if resource["name"] == resource_name:
            selectors = resource.get("selector", {})
            return resource_type in selectors.get("types", [resource_type]) and (
                selectors.get("labels") is None
                or any({l: v} in selectors.get("labels") for l, v in labels.items())
            )
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
):
    if event_info[0].timestamp() > STARTUP_TIME.timestamp():
        # Send notification
        notifs = []
        for group_name, group in kube_notify_config.get("notifications", {}).items():
            if check_selector(
                resource_name, group.get("resources"), resource_type, labels
            ):
                if group.get("discord"):
                    notifs.append(f"{group_name}/discord")
                    # send_discord_webhook(group.get("discord")["webhook"], title, description, fields, group.get("discord").get("username"), group.get("discord").get("avatar_url"))
                if group.get("gotify"):
                    notifs.append(f"{group_name}/gotify")
                    # send_gotify_message(group.get("gotify")["webhook"], title, description, fields)
        logger.info(
            f"[{','.join(notifs) or 'Unhandled'}] {event_info[0]} > {STARTUP_TIME} {description}"
        )
    else:
        logger.debug(f"[Skipping] {event_info[0]} < {STARTUP_TIME} {description}")


def send_gotify_message(url, token, title, description, fields):
    # Construct the HTTP request for sending a message to Gotify
    url = f"{url}/message?token={token}"
    headers = {"Content-Type": "application/json"}
    message = description + "\n"
    i = 0
    for key, value in fields.items():
        if i % 2:
            message += "\n"
        else:
            message += " | "
        message += f"{key}: {value}"
        i += 1
    data = {"title": title, "message": message}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        logger.error("Failed to send notification to Gotify")


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
        logger.error("Failed to send notification to Discord")
