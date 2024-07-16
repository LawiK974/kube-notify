import datetime

import yaml


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


def add_fields_to_the_message(obj: dict, crd: dict) -> dict[str, str]:
    # add fields to Message
    fields = {}
    for key, yaml_path in crd.get("includeFields", {}).items():
        field = obj.copy()
        for yaml_key in yaml_path.split("."):
            field = field.get(yaml_key, {})
        fields[key] = str(field)
    return fields


def load_kube_notify_config(config_path: str) -> dict:
    with open(config_path) as f:
        kube_notify_config = yaml.safe_load(f)
    return kube_notify_config
