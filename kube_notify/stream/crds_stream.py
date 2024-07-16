import asyncio
import datetime

from kubernetes_asyncio import client

import kube_notify.notifications as notifs
from kube_notify.utils import logger, misc


async def crds_stream(
    crd: dict, namespace: str, kube_notify_config: dict, iterate: bool = True
) -> None:
    async with client.ApiClient() as api:
        last_event_info = None
        # Watch Velero Backups
        crd_group, crd_version, crd_plural = crd.get("type").split("/")
        crds_api = client.CustomObjectsApi(api)
        event_infos = set()
        first_loop = True
        while iterate or first_loop:
            first_loop = False
            try:
                logger.logger.debug(f"Strating New loop for crds {crd.get('type')}")
                stream = None
                if namespace:
                    stream = await crds_api.list_namespaced_custom_object(
                        crd_group, crd_version, namespace, crd_plural, watch=False
                    )
                else:
                    stream = await crds_api.list_cluster_custom_object(
                        crd_group, crd_version, crd_plural, watch=False
                    )
                for obj in stream["items"]:
                    resource_name = str(obj["metadata"]["name"])
                    resource_namespace = str(obj["metadata"]["namespace"])
                    resource_kind = str(obj["kind"])
                    resource_apiversion = str(obj["apiVersion"])
                    creation_timestamp = datetime.datetime.strptime(
                        obj["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
                    )

                    # add fields to Message
                    fields = misc.add_fields_to_the_message(obj, crd)
                    last_timestamp = misc.process_last_timestamp(obj, crd)
                    fields["Timestamp"] = last_timestamp.isoformat()
                    fields["Namespace"] = resource_namespace
                    event_type = (
                        "ADDED" if creation_timestamp == last_timestamp else "UPDATED"
                    )
                    title = f"{resource_apiversion} {resource_kind} {event_type}"
                    description = f"{resource_apiversion} {resource_kind} {resource_name} {event_type}."
                    event_info = (
                        last_timestamp,
                        resource_apiversion,
                        resource_kind,
                        resource_name,
                        resource_namespace,
                    )
                    if event_info in event_infos or last_event_info == event_info:
                        continue
                    event_infos.add(event_info)
                    last_event_info = event_info
                    # logger.logger.info(event)
                    await notifs.handle_notify(
                        "customResources",
                        title,
                        description,
                        fields,
                        event_info,
                        kube_notify_config,
                        crd.get("type"),
                        dict(obj["metadata"].get("labels", {})),
                        resource_namespace,
                    )
                    await asyncio.sleep(0)
                del stream
            except Exception as e:
                logger.logger.error(f"{type(e).__name__}: {e}")
                if not iterate:
                    raise e
            iterate and await asyncio.sleep(crd.get("pollingIntervalSeconds", 60))
