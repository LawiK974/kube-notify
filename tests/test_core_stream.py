# from pytest_mock import MockerFixture  # AsyncMockType,
import unittest.mock as mock

import pytest

from kube_notify import __version__
from kube_notify.app import (
    core_stream,  # Adjust the import according to your app's structure
)

from .utils.core_stream import fake_core_events_list, fake_pod

# import datetime


def test_version():
    assert __version__ == "0.0.0"


@pytest.fixture
def kube_notify_config():
    return {
        "events": {
            "coreApiEvents": {
                "pollingIntervalSeconds": 60,
            }
        }
    }


@pytest.fixture
def mock_list_events(mocker):
    async_mock = mock.AsyncMock()
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.list_event_for_all_namespaces",
        side_effect=async_mock,
    )
    # mocker.patch("kube_notify.logger.logger")
    return async_mock


@pytest.fixture
def mock_list_pod(mocker):
    async_mock = mock.AsyncMock()
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.read_namespaced_pod",
        side_effect=async_mock,
    )
    # mocker.patch("kube_notify.logger.logger")
    return async_mock


@pytest.mark.asyncio
async def test_core_stream(mock_list_events, mock_list_pod, kube_notify_config):
    # Mock the list_event_for_all_namespaces method to return a mock event
    mock_list_events.return_value = fake_core_events_list()
    mock_list_pod.return_value = fake_pod()
    await core_stream(kube_notify_config, iterate=False)
