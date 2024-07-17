# import datetime

from kubernetes_asyncio import client


def find_container_restart_policy(
    containers: list[client.V1Container], container_name: str, pod_name: str
) -> str:
    for container in containers:
        if container.name == container_name:
            return container.restart_policy
    raise KeyError(f"{container_name} not found in containers for pod {pod_name}")


def get_container_state(restart_policy: str | None, exit_code: int) -> tuple[bool, str]:
    if restart_policy in ["Always", None] or (
        restart_policy == "OnFailure" and exit_code != 0
    ):
        return True, "restarted"
    if restart_policy == "Never" and exit_code != 0:
        return True, "crashed"
    if exit_code == 0:
        return False, "finished"
    return False, ""


async def generate_pod_termination_events(
    api: client.CoreV1Api,
) -> list[client.CoreV1Event]:
    events = []
    pods: client.V1PodList = await api.list_pod_for_all_namespaces()
    for pod in pods.items:
        containers = (
            pod.spec.containers
            or [] + pod.spec.init_containers
            or [] + pod.spec.ephemeral_containers
            or []
        )
        for container_status in (
            pod.status.container_statuses
            or [] + pod.status.ephemeral_container_statuses
            or [] + pod.status.init_container_statuses
            or []
        ):
            namespace = pod.metadata.namespace
            pod_name = pod.metadata.name
            restart_count = container_status.restart_count
            container_name = container_status.name
            status = container_status.last_state
            restart_policy = find_container_restart_policy(
                containers, container_name, pod_name
            )
            if status.terminated is None:
                continue
            exit_code = int(status.terminated.exit_code)
            is_error, state = get_container_state(restart_policy, exit_code)
            # see doc here
            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ContainerStateTerminated.md
            if is_error:
                reason = status.terminated.reason
                timestamp = status.terminated.finished_at
                message = status.terminated.message
                events.append(
                    client.CoreV1Event(
                        kind="Event",
                        type="Error",
                        metadata=client.V1ObjectMeta(
                            name=f"{pod_name}.{container_name}.{restart_count}",
                            namespace=namespace,
                        ),
                        reason=reason,
                        last_timestamp=timestamp,
                        message=message
                        or f"{reason}({exit_code}): Container {container_name} {state} (restartCount: {restart_count})",
                        involved_object=client.V1ObjectReference(
                            kind="Pod", name=pod_name, namespace=namespace
                        ),
                    )
                )
    return events
