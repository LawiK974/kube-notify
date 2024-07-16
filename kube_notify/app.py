import asyncio
import os

from kubernetes_asyncio import config

import kube_notify
from kube_notify.stream import core_stream, crds_stream
from kube_notify.utils import logger, misc


def start_kube_notify_loop(kube_notify_config: dict, iterate: bool = True) -> None:
    logger.logger.info(
        f"Starting kube-notify {kube_notify.__version__} at {kube_notify.STARTUP_TIME}"
    )
    logger.logger.info(f"PYTHONUNBUFFERED={os.environ['PYTHONUNBUFFERED']}")
    tasks = []
    if kube_notify_config["events"].get("coreApiEvents").get("enabled"):
        logger.logger.info("Creating watcher for coreApiEvents")
        tasks.append(
            asyncio.ensure_future(core_stream.core_stream(kube_notify_config, iterate))
        )

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
                        crds_stream.crds_stream(
                            crd, namespace, kube_notify_config, iterate
                        )
                    )
                )
        else:
            error = f"Couldn't get CRD type from 'customResources' at index {index}"
            logger.logger.error(error)
            raise ValueError(error)
    try:
        kube_notify.ioloop.run_until_complete(asyncio.wait(tasks))
        # kube_notify.ioloop.run_forever()
    except Exception as e:
        logger.logger.error("[Error] Ignoring :" + e)
    finally:
        kube_notify.ioloop.run_until_complete(kube_notify.ioloop.shutdown_asyncgens())
        kube_notify.ioloop.close()


def main() -> None:
    args = kube_notify.parser.parse_args()
    # Initialize Kubernetes client
    if args.inCluster:
        config.load_incluster_config()
    else:
        kube_notify.ioloop.run_until_complete(
            config.load_kube_config(context=args.context)
        )
    kube_notify_config = misc.load_kube_notify_config(args.config)
    start_kube_notify_loop(kube_notify_config)


if __name__ == "__main__":
    main()
