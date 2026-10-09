"""Exercise included FastAPI routes with the real metrics middleware, without GPU."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient
    from prometheus_fastapi_instrumentator import Instrumentator

    app = FastAPI()
    router = APIRouter()

    @router.get('/health')
    def health():
        return {'status': 'synthetic-http-fixture'}

    app.include_router(router)
    nested = APIRouter(prefix='/v1')
    nested.include_router(router)
    app.include_router(nested)
    Instrumentator().instrument(app).expose(app)
    results = []
    with TestClient(app, raise_server_exceptions=False) as client:
        for route, status in [('/health', 200), ('/v1/health', 200), ('/missing', 404), ('/metrics', 200)]:
            response = client.get(route)
            results.append({'route': route, 'expected': status, 'actual': response.status_code,
                            'passed': response.status_code == status})
    passed = all(row['passed'] for row in results)
    (args.output / 'receipt.json').write_text(json.dumps({
        'status': 'http_stack_passed' if passed else 'http_stack_failed',
        'versions': {name: version(name) for name in
                     ['fastapi', 'starlette', 'prometheus-fastapi-instrumentator', 'httpx']},
        'checks': results,
        'scope': 'Real HTTP middleware with synthetic included routes; no vLLM generation'}, indent=2)+'\n')
    print('HTTP middleware checks:', 'passed' if passed else 'failed', flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
