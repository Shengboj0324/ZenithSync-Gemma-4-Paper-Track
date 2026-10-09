
import json
from pathlib import Path
items=[];reports=[];collection_errors=[]
resource_events=[]
def pytest_configure(config):
    cache=Path('/audit/resources.json')
    if cache.exists():
        import base64
        from offline_resources import install_resource_replay
        resources=json.loads(cache.read_text())
        install_resource_replay({url:(base64.b64decode(value['body']),value['sha256'])
            for url,value in resources.items()},resource_events)
def pytest_collection_finish(session):
    items.extend(item.nodeid for item in session.items)
def pytest_collectreport(report):
    if report.failed:
        collection_errors.append({'nodeid':report.nodeid,'error':str(report.longrepr)[:4000]})
def pytest_runtest_logreport(report):
    reports.append({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome})
def pytest_sessionfinish(session,exitstatus):
    Path('/audit/outcomes.json').write_text(json.dumps({'collected':items,'reports':reports,
        'collection_errors':collection_errors,'exitstatus':int(exitstatus)}))
    Path('/audit/resource-events.json').write_text(json.dumps(resource_events))
