import kube_notify
import kube_notify.discord as discord
import kube_notify.gotify as gotify
import kube_notify.logger as logger
import kube_notify.selectors as selectors


def get_status_icon(event_type: str, fields: dict) -> str:
    if event_type == "Warning":
        return "⚠️"
    if event_type == "Normal":
        return "✅"
    if fields.get("Status") == "Completed":
        return "✅"
    if fields.get("Status") == "InProgress":
        return "⏳"
    if fields.get("Status") == "New":
        return "🆕"
    if fields.get("Status") == "PartiallyFailed":
        return "⚠️"
    if fields.get("Status") == "Failed":
        return "❌"
    return ""


async def handle_notify(
    resource_name: str,
    title: str,
    description: str,
    fields: dict,
    event_info: str,
    kube_notify_config: dict,
    resource_type: str,
    labels: dict,
    namespace: str,
    involved_object_kind: str = None,
    reason: str = None,
) -> None:
    notifs = ["Skipping"]
    status_icon = get_status_icon(resource_type, fields)
    description = f"[{status_icon}] {description}"
    if event_info[0].timestamp() > kube_notify.STARTUP_TIME.timestamp():
        # Send notification
        notifs = ["Excluded"]
        for group_name, group in kube_notify_config.get("notifications", {}).items():
            if selectors.check_selector(
                resource_name,
                group.get("resources"),
                resource_type,
                labels,
                namespace,
                involved_object_kind,
                reason,
            ):
                notifs = []
                if group_values := group.get("discord"):
                    notifs.append(f"{group_name}/discord")
                    discord.send_discord_webhook(
                        group_values["webhook"],
                        title,
                        description,
                        fields,
                        group_values.get("username"),
                        group_values.get("avatar_url"),
                    )
                if group_values := group.get("gotify"):
                    notifs.append(f"{group_name}/gotify")
                    gotify.send_gotify_message(
                        group_values["url"],
                        group_values["token"],
                        title,
                        description,
                        fields,
                    )
    logger.logger.info(f"{event_info[0]} [{','.join(notifs)}] {description}")
