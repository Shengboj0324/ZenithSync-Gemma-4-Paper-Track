
import json
from pathlib import Path
items=[];reports=[];collection_errors=[]
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
