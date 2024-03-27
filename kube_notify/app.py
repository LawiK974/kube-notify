import asyncio
import datetime

import kubernetes_asyncio
import yaml

import kube_notify
import kube_notify.logger as logger
import kube_notify.notifications as notifs


def process_last_timestamp(obj: dict, crd: dict) -> datetime.datetime:
    # Process last timestamp for event
    # can be calculated using different fields if available (by order of priority)
    for yaml_path in crd.get("lastTimestamp").split("|"):
        value = obj.copy()
        for key in yaml_path.strip(" ").split("."):
            value = value.get(key, {})
        if value:
            last_timestamp = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            break
    return last_timestamp


def add_fields_to_the_message(obj: dict, crd: dict) -> dict:
    # add fields to Message
    fields = {}
    for key, yaml_path in crd.get("includeFields", {}).items():
        field = obj.copy()
        for yaml_key in yaml_path.split("."):
            field = field.get(yaml_key, {})
        fields[key] = str(field)
    return fields


async def crds_stream(crd: dict, namespace: str, kube_notify_config: dict) -> None:
    async with kubernetes_asyncio.client.ApiClient() as api:
        last_event_info = None
        # Watch Velero Backups
        crd_group, crd_version, crd_plural = crd.get("type").split("/")
        crds_api = kubernetes_asyncio.client.CustomObjectsApi(api)
        event_infos = set()
        while True:
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
                    fields = add_fields_to_the_message(obj, crd)
                    last_timestamp = process_last_timestamp(obj, crd)
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
            await asyncio.sleep(crd.get("pollingIntervalSeconds", 60))


async def core_stream(kube_notify_config: dict) -> None:
    async with kubernetes_asyncio.client.ApiClient() as api:
        last_event_info = None
        core_api = kubernetes_asyncio.client.CoreV1Api(api)
        event_infos = set()
        while True:
            try:
                logger.logger.debug("Strating New loop for core api")
                stream = await core_api.list_event_for_all_namespaces(watch=False)
                for obj in stream.items:
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
            except Exception as e:
                logger.logger.error(f"{type(e).__name__}: {e}")
            await asyncio.sleep(
                kube_notify_config["events"]["coreApiEvents"].get(
                    "pollingIntervalSeconds", 60
                )
            )


def load_kube_notify_config(config_path: str) -> dict:
    with open(config_path) as f:
        kube_notify_config = yaml.safe_load(f)
    return kube_notify_config


def main() -> None:
    args = kube_notify.parser.parse_args()
    logger.logger.info(
        f"Starting kube-notify {kube_notify.__version__} at {kube_notify.STARTUP_TIME}"
    )
    # Initialize Kubernetes client
    ioloop = asyncio.get_event_loop()
    if args.inCluster:
        kubernetes_asyncio.config.load_incluster_config()
    else:
        ioloop.run_until_complete(
            kubernetes_asyncio.config.load_kube_config(context=args.context)
        )

    kube_notify_config = load_kube_notify_config(args.config)
    tasks = []
    if kube_notify_config["events"].get("coreApiEvents").get("enabled"):
        logger.logger.info("Creating watcher for coreApiEvents")
        tasks.append(asyncio.ensure_future(core_stream(kube_notify_config)))

    for index, crd in enumerate(
        kube_notify_config.get("events").get("customResources", [])
    ):
        # loop to watch crds
        if crd.get("type"):
            for namespace in crd.get("namespaces", [None]):
                logger.logger.info(
                    f"Creating watcher for crd {crd.get('type')} {namespace}"
                )
                tasks.append(
                    asyncio.ensure_future(
                        crds_stream(crd, namespace, kube_notify_config)
                    )
                )
        else:
            error = f"Couldn't get CRD type from 'customResources' at index {index}"
            logger.logger.error(error)
            raise ValueError(error)
    try:
        ioloop.run_until_complete(asyncio.wait(tasks))
        ioloop.run_forever()
    except Exception as e:
        logger.logger.error("[Error] Ignoring :" + e)
    finally:
        ioloop.run_until_complete(ioloop.shutdown_asyncgens())
        ioloop.close()


if __name__ == "__main__":
    main()
