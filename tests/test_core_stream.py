# flake8: noqa: F401, F811;
import pytest
from kubernetes_asyncio import client

from kube_notify import __version__, app
from kube_notify.utils import misc

from . import CONFIG, utils
from .mock_func import (
    mock_config_kube,
    mock_list_crds,
    mock_list_events,
    mock_list_pods,
    mock_read_pod,
    mock_requests_post,
    requests_post,
)


def test_version():
    assert __version__ == "0.0.0"


@pytest.mark.parametrize(
    ("event_name"),
    utils.EVENTS.keys(),
)
def test_app_single(
    event_name,
    mock_list_events,
    mock_list_crds,
    mock_read_pod,
    mock_list_pods,
    mock_config_kube,
    mock_requests_post,
    caplog,
):
    # test all events one by one
    event = utils.EVENTS[event_name]
    mock_list_events.return_value = client.CoreV1EventList(
        items=[event.get("event")] if event.get("event") else []
    )
    result = []
    mock_requests_post.side_effect = requests_post(result)
    kube_notify_config = misc.load_kube_notify_config(CONFIG)
    app.start_kube_notify_loop(kube_notify_config, in_cluster=False, iterate=False)
    assert any(event["log_message"] in message for message in caplog.messages)


def test_app_all(
    mock_list_events,
    mock_list_crds,
    mock_read_pod,
    mock_list_pods,
    mock_requests_post,
    mock_config_kube,
    caplog,
):
    # Mock the list_event_for_all_namespaces method to return a mock event
    events = []
    log_messages = []
    for event in utils.EVENTS.values():
        if event["event"]:
            events.append(event["event"])
        log_messages.append(event["log_message"])
    mock_list_events.return_value = client.CoreV1EventList(items=events)
    result = []
    mock_requests_post.side_effect = requests_post(result)
    kube_notify_config = misc.load_kube_notify_config(CONFIG)
    app.start_kube_notify_loop(kube_notify_config, in_cluster=False, iterate=False)
    assert all(log_message in caplog.text for log_message in log_messages)
