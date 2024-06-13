import argparse
import datetime

__version__ = "0.0.0"
STARTUP_TIME = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
type EventInfo = tuple[datetime.datetime, str, str, str, str, str, str, str]
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
