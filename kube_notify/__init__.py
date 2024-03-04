import datetime
import argparse

STARTUP_TIME = datetime.datetime.utcnow()

parser = argparse.ArgumentParser(
    prog="kube-notify",
    description="An app that watches kubernetes resource creation, deletion, updates and errors events and notify selected events to gotify.",
    epilog="Made with passion by LawiK974.",
)

parser.add_argument("-c", "--config", type=str, help="Path to the config file")
parser.add_argument("--inCluster", action="store_true", help="Running in cluster")
