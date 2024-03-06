import asyncio
import datetime

import yaml
from kubernetes_asyncio import client, config

from kube_notify import parser
from kube_notify.logger import logger
from kube_notify.notifications import (  # send_discord_webhook,; send_gotify_message,
    handle_notify,
)


def process_last_timestamp(obj, crd):
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


def add_fields_to_the_message(obj, crd):
    # add fields to Message
    fields = {}
    for key, yaml_path in crd.get("includeFields", {}).items():
        field = obj.copy()
        for key in yaml_path.split("."):
            field = field.get(key, {})
        fields[key] = field
    return fields


async def crds_stream(crd, namespace, kube_notify_config):
    async with client.ApiClient() as api:
        last_event_info = None
        # Watch Velero Backups
        crd_group, crd_version, crd_plural = crd.get("type").split("/")
        crds_api = client.CustomObjectsApi(api)
        event_infos = set()
        while True:
            logger.debug(f"Strating New loop for crds {crd.get('type')}")
            stream = None
            if namespace:
                stream = await crds_api.list_namespaced_custom_object(
                    crd_group, crd_version, namespace, crd_plural, watch=False
                )
            else:
                stream = await crds_api.list_cluster_custom_object(
                    crd_group, crd_version, crd_plural, watch=False
                )
            for event in stream["items"]:
                obj = event
                resource_name = obj["metadata"]["name"]
                resource_kind = obj["kind"]
                resource_apiversion = obj["apiVersion"]
                creation_timestamp = datetime.datetime.strptime(
                    obj["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
                )

                # add fields to Message
                fields = add_fields_to_the_message(obj, crd)
                last_timestamp = process_last_timestamp(obj, crd)
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
                )
                if event_info in event_infos or last_event_info == event_info:
                    continue
                event_infos.add(event_info)
                last_event_info = event_info
                # logger.info(event)
                await handle_notify(
                    "customResources",
                    title,
                    description,
                    fields,
                    event_info,
                    kube_notify_config,
                    crd.get("type"),
                    dict(obj["metadata"].get("labels", {})),
                )
                await asyncio.sleep(0)
            await asyncio.sleep(crd.get("pollingIntervalSeconds", 60))


async def core_stream(kube_notify_config):
    async with client.ApiClient() as api:
        last_event_info = None
        core_api = client.CoreV1Api(api)
        event_infos = set()
        while True:
            logger.debug("Strating New loop for core api")
            stream = await core_api.list_event_for_all_namespaces(watch=False)
            for obj in stream.items:
                event_type = obj.type
                resource_name = obj.metadata.name
                resource_kind = obj.kind or "Event"
                last_timestamp = (
                    obj.last_timestamp or obj.event_time or obj.creation_timestamp
                ).replace(tzinfo=None)
                message = obj.message
                title = f"{resource_kind} {event_type}"
                description = f"{event_type} {resource_kind} : {obj.involved_object.kind} {obj.involved_object.name} {obj.reason}."
                fields = {
                    "Reason": obj.reason,
                    "Type": obj.type,
                    "Message": message,
                    "Involved Object kind": obj.involved_object.kind,
                    "Involved Object name": obj.involved_object.name,
                    "Namespace": obj.metadata.namespace,
                }
                event_info = (
                    last_timestamp,
                    obj.type,
                    resource_kind,
                    obj.reason,
                    resource_name,
                    event_type,
                    message,
                )
                if event_info in event_infos or last_event_info == event_info:
                    continue
                event_infos.add(event_info)
                last_event_info = event_info
                await handle_notify(
                    "coreApiEvents",
                    title,
                    description,
                    fields,
                    event_info,
                    kube_notify_config,
                    "v1/events",
                    dict(obj.metadata.labels or {}),
                )
                await asyncio.sleep(0)
            await asyncio.sleep(
                kube_notify_config["events"]["coreApiEvents"].get(
                    "pollingIntervalSeconds", 60
                )
            )


def load_kube_notify_config(config_path):
    with open(config_path) as f:
        kube_notify_config = yaml.safe_load(f)
    return kube_notify_config


def main():
    args = parser.parse_args()
    # Initialize Kubernetes client
    ioloop = asyncio.get_event_loop()
    if args.inCluster:
        ioloop.run_until_complete(config.load_incluster_config(context=args.context))
    else:
        ioloop.run_until_complete(config.load_kube_config(context=args.context))

    kube_notify_config = load_kube_notify_config(args.config)
    tasks = []
    if kube_notify_config["events"].get("coreApiEvents").get("enabled"):
        logger.info("Creating watcher for coreApiEvents")
        tasks.append(asyncio.ensure_future(core_stream(kube_notify_config)))

    for index, crd in enumerate(
        kube_notify_config.get("events").get("customResources", [])
    ):
        # loop to watch crds
        if crd.get("type"):
            for namespace in crd.get("namespaces", [None]):
                logger.info(f"Creating watcher for crd {crd.get('type')} {namespace}")
                tasks.append(
                    asyncio.ensure_future(
                        crds_stream(crd, namespace, kube_notify_config)
                    )
                )
        else:
            error = f"Couldn't get CRD type from 'customResources' at index {index}"
            logger.error(error)
            raise ValueError(error)
    try:
        ioloop.run_until_complete(asyncio.wait(tasks))
        ioloop.run_forever()
    except Exception as e:
        logger.error("[Error] Ignoring :" + e)
    finally:
        ioloop.run_until_complete(ioloop.shutdown_asyncgens())
        ioloop.close()


if __name__ == "__main__":
    main()
