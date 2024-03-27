import argparse
import datetime
import importlib.metadata

__version__ = importlib.metadata.version(__name__)
STARTUP_TIME = datetime.datetime.utcnow()

parser = argparse.ArgumentParser(
    prog=f"kube-notify-{__version__}",
    description="An app that watches kubernetes resource creation, deletion, updates and errors events and notify selected events to gotify.",
    epilog="Made with passion by LawiK974.",
)

parser.add_argument("-c", "--config", type=str, help="Path to the config file")
parser.add_argument("--version", action="version", version=__version__)
parser.add_argument("--inCluster", action="store_true", help="Running in cluster")
parser.add_argument(
    "--context",
    type=str,
    help="Kube config context to use (check `kubectl config current-context`)",
)
