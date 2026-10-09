"""Observable cleanup for an explicitly owned container; uncertainty is retained."""


def cleanup_owned_container(manager, container_id):
    report = {'container_id': container_id, 'removed': None, 'errors': []}
    try:
        manager.stop(container_id)
    except Exception as error:
        report['errors'].append({'operation': 'stop', 'type': type(error).__name__})
    try:
        remaining = manager.client.containers.list(all=True, filters={'id': container_id})
        report['removed'] = not remaining
    except Exception as error:
        report['errors'].append({'operation': 'verify_absence', 'type': type(error).__name__})
    return report
