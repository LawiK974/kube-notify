# import asyncio
import datetime

import yaml
from kubernetes_asyncio import client


def fake_pods() -> dict[str, client.V1Pod]:
    with open("tests/data/pods.yaml") as f:
        pods = yaml.safe_load(f)
    items = {}
    for pod_name, pod in pods.items():
        items[pod_name] = client.V1Pod(
            kind="Pod",
            metadata=client.V1ObjectMeta(
                name=pod_name,
                namespace=pod.get("namespace", "default"),
                labels=pod.get("labels", {}),
            ),
            spec=client.V1PodSpec(
                node_name=pod["node"],
                containers=[client.V1Container(**e) for e in pod.get("containers", [])],
            ),
            status=client.V1PodStatus(
                container_statuses=[
                    client.V1ContainerStatus(
                        **{
                            **e,
                            "last_state": client.V1ContainerState(
                                terminated=(
                                    client.V1ContainerStateTerminated(
                                        **{
                                            "finished_at": (
                                                datetime.datetime.now(
                                                    datetime.UTC
                                                ).replace(tzinfo=None)
                                            ),
                                            **e.get("last_state", {}).get("terminated"),
                                        }
                                    )
                                    if e.get("last_state", {}).get("terminated")
                                    else None
                                )
                            ),
                        }
                    )
                    for e in pod.get("container_statuses", [])
                ]
            ),
        )
    return items


def fake_core_events_list() -> dict:
    with open("tests/data/events.yaml") as f:
        events = yaml.safe_load(f)

    items = events.copy()
    for event_name, event in events.items():
        event_time = (
            datetime.datetime.strptime(event.get("timestamp"))
            if event.get("timestamp")
            else datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        )
        items[event_name]["event"] = (
            None
            if "type" not in event
            else client.CoreV1Event(
                type=event["type"],
                kind="Event",
                last_timestamp=event_time,
                metadata=client.V1ObjectMeta(
                    name=event_name,
                    creation_timestamp=event_time,
                ),
                involved_object=client.V1ObjectReference(
                    **event.get("involved_object")
                ),
                reason=event["reason"],
                message=event["message"],
            )
        )
    return items
