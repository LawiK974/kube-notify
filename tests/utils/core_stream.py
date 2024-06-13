# import asyncio
import datetime

from kubernetes_asyncio import client


def fake_pod():
    mock_pod = client.V1Pod(
        kind="Pod",
        metadata=client.V1ObjectMeta(
            name="test-pod",
            namespace="default",
            labels={"app": "test"},
        ),
    )
    return mock_pod


def fake_core_events_list():
    event_time = datetime.datetime.now()
    mock_event = client.CoreV1Event(
        type="Normal",
        kind="Event",
        last_timestamp=event_time,
        metadata=client.V1ObjectMeta(
            name="test-event",
            creation_timestamp=event_time,
        ),
        involved_object=client.V1ObjectReference(
            kind="Pod", name="test-pod", namespace="default"
        ),
        reason="Created",
        message="This is a test event",
    )
    return client.CoreV1EventList(items=[mock_event])
