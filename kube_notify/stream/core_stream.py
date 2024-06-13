import asyncio
import datetime

from kubernetes_asyncio import client

import kube_notify.notifications as notifs
from kube_notify.utils import logger

from . import pod_terminations


async def core_stream(kube_notify_config: dict, iterate: bool = True) -> None:
    async with client.ApiClient() as api:
        last_event_info = None
        core_api = client.CoreV1Api(api)
        event_infos = set()
        first_loop = True
        while iterate or first_loop:
            first_loop = False
            try:
                logger.logger.debug("Strating New loop for core api")
                stream: client.CoreV1EventList = (
                    await core_api.list_event_for_all_namespaces(watch=False)
                )
                stream_items = stream.items
                if kube_notify_config["events"]["coreApiEvents"].get(
                    "addPodTerminationErrors"
                ):
                    stream_items += (
                        await pod_terminations.generate_pod_termination_events(core_api)
                    )
                for obj in stream_items:
                    event_type = str(obj.type)
                    resource_name = str(obj.metadata.name)
                    resource_kind = str(obj.kind or "Event")
                    last_timestamp = datetime.datetime.fromisoformat(
                        (obj.last_timestamp or obj.event_time or obj.creation_timestamp)
                        .replace(tzinfo=None)
                        .isoformat()
                    )
                    message = str(obj.message)
                    reason = str(obj.reason)
                    involved_object_kind = str(obj.involved_object.kind)
                    involved_object_name = str(obj.involved_object.name)
                    involved_object_namespace = str(obj.involved_object.namespace)

                    title = f"{event_type} {resource_kind}"
                    description = (
                        f"{involved_object_kind} {involved_object_name} {reason}."
                    )
                    fields = {
                        "Message": message,
                        "Reason": reason,
                        "Type": event_type,
                        "Object kind": involved_object_kind,
                        "Object name": involved_object_name,
                        "Timestamp": last_timestamp.isoformat(),
                        "Namespace": involved_object_namespace,
                    }
                    event_info = (
                        last_timestamp,
                        involved_object_namespace,
                        event_type,
                        involved_object_kind,
                        involved_object_name,
                        reason,
                        resource_name,
                        message,
                    )
                    labels = dict(obj.metadata.labels or {})
                    if event_info in event_infos or last_event_info == event_info:
                        continue
                    elif involved_object_kind == "Pod":
                        try:
                            pod = await core_api.read_namespaced_pod(
                                involved_object_name, involved_object_namespace
                            )
                            labels.update(dict(pod.metadata.labels or {}))
                            fields.update({"Node": pod.spec.node_name})
                        except Exception:
                            pass
                    event_infos.add(event_info)
                    last_event_info = event_info
                    await notifs.handle_notify(
                        "coreApiEvents",
                        title,
                        description,
                        fields,
                        event_info,
                        kube_notify_config,
                        event_type,
                        labels,
                        involved_object_namespace,
                        involved_object_kind,
                        reason,
                    )
                    await asyncio.sleep(0)
                del stream
            except Exception as e:  # pragma: no cover
                logger.logger.error(f"{type(e).__name__}: {e}")
                if not iterate:
                    raise e
            iterate and await asyncio.sleep(
                kube_notify_config["events"]["coreApiEvents"].get(
                    "pollingIntervalSeconds", 60
                )
            )
