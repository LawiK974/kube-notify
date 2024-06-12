import json

import requests

import kube_notify.logger as logger


def send_mattermost_message(
    webhook: str,
    title: str,
    description: str,
    fields: dict,
    channel: str | None = None,
    username: str | None = None,
    icon_url: str | None = None,
) -> None:
    # Construct the HTTP request for sending a message to Mattermost
    headers = {"Content-Type": "application/json"}
    message = f"#### {title} : {description}\n"

    for key, value in fields.items():
        message += f"**{key} :** {value}\n"
    data = {"text": message}
    channel and data.update({"channel": channel})
    username and data.update({"username": username})
    icon_url and data.update({"icon_url": icon_url})
    response = requests.post(webhook, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        logger.logger.error(
            f"[{response.status_code}] Failed to send notification to Mattermost : {str(response.content)}"
        )
