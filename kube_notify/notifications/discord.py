import json

import requests

from kube_notify.utils import logger


def send_discord_webhook(
    webhook_url: str,
    title: str,
    description: str,
    fields: dict[str, str],
    username: str = "kube-notify",
    avatar_url: str = None,
) -> None:
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
