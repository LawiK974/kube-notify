import json

import requests

from kube_notify.utils import logger


def send_gotify_message(
    url: str, token: str, title: str, description: str, fields: dict[str, str]
) -> None:
    # Construct the HTTP request for sending a message to Gotify
    url = f"{url}/message?token={token}&format=markdown"
    headers = {"Content-Type": "application/json"}
    message = f"**{description}**\\\n"

    for key, value in fields.items():
        message += f"**{key} : **{value}\\\n"
    data = {
        "title": title,
        "message": message,
        "extras": {"client::display": {"contentType": "text/markdown"}},
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        logger.logger.error("Failed to send notification to Gotify")
