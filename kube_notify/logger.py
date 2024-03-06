import logging
import sys

from kube_notify import STARTUP_TIME

logger = logging.getLogger("k8s_events")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.info(f"Starting kube-notify at {STARTUP_TIME}")
