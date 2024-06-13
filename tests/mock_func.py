import unittest.mock as mock

import pytest
import requests
from kubernetes_asyncio import client

from .utils import PODS, core_stream


@pytest.fixture
def mock_config_kube(mocker):
    async_mock = mock.AsyncMock()
    mocker.patch(
        "kubernetes_asyncio.config.load_kube_config",
        side_effect=async_mock,
        return_value=None,
    )
    return async_mock


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
def mock_list_crds(mocker):
    async_mock = mock.AsyncMock()
    mocker.patch(
        "kubernetes_asyncio.client.CustomObjectsApi.list_namespaced_custom_object",
        side_effect=async_mock,
        return_value={"items": []},
    )
    # mocker.patch("kube_notify.logger.logger")
    return async_mock


async def read_namespaced_pod(name, namespace, **kwargs):
    pod = PODS.get(name)
    assert pod is None or pod.metadata.namespace == namespace
    return pod


@pytest.fixture
def mock_read_pod(mocker):
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.read_namespaced_pod",
        side_effect=read_namespaced_pod,
    )
    return read_namespaced_pod


@pytest.fixture
def mock_list_pods(mocker):
    async_mock = mock.AsyncMock()
    mocker.patch(
        "kubernetes_asyncio.client.CoreV1Api.list_pod_for_all_namespaces",
        side_effect=async_mock,
    )
    async_mock.return_value = client.V1PodList(items=core_stream.fake_pods().values())
    return async_mock


def requests_post(result: list):
    def result_func(url, data, headers):
        result.append({"args": (url, data, headers)})
        response = requests.Response()
        response.status_code = 201
        return response

    return result_func


@pytest.fixture
def mock_requests_post(mocker):
    mock_func = mock.Mock()
    mocker.patch("requests.post", side_effect=mock_func)
    return mock_func
