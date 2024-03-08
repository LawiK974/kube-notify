import logging
import sys

import kube_notify

logger = logging.getLogger("k8s_events")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.info(f"Starting kube-notify at {kube_notify.STARTUP_TIME}")
