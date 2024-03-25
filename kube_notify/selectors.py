def check_selector(
    resource_name: str,
    resources: list[dict],
    resource_type: str,
    labels: dict,
    namespace: str,
    involved_object_kind: str,
    reason: str,
) -> bool:
    for resource in resources:
        if resource["name"] == resource_name:
            result = True
            if "selector" in resource:
                selectors = resource.get("selector", {})
                result = (
                    resource_type in selectors.get("types", [resource_type])
                    and (
                        selectors.get("labels") is None
                        or any(
                            (
                                label.get("key"),
                                label.get("value", labels.get(label.get("key"))),
                            )
                            in labels.items()
                            for label in selectors.get("labels", [])
                        )
                    )
                    and (
                        selectors.get("involvedObjectKind") is None
                        or involved_object_kind in selectors.get("involvedObjectKind")
                    )
                    and (
                        selectors.get("namespaces") is None
                        or namespace in selectors.get("namespaces")
                    )
                    and (
                        selectors.get("reasons") is None
                        or reason in selectors.get("reasons")
                    )
                )
            elif "excludeSelector" in resource:
                selectors = resource.get("excludeSelector", {})
                result = not (
                    resource_type in selectors.get("types", [])
                    or any(
                        (
                            label.get("key"),
                            label.get("value", labels.get(label.get("key"))),
                        )
                        in labels.items()
                        for label in selectors.get("labels", [])
                    )
                    or involved_object_kind in selectors.get("involvedObjectKind", [])
                    or namespace in selectors.get("namespaces", [])
                    or reason in selectors.get("reasons", [])
                )
            if result:
                return result
    return False
