"""Explicit evaluator-only replay of immutable HTTP response bodies.

This adapter is a qualification aid, not a general HTTP cache. It supports
only body reads through urllib.urlopen and requests.get. Unknown resources
and request options fail closed; production/agent networking is unaffected.
"""

import hashlib
import io
import ssl
from email.message import Message
from urllib.response import addinfourl


def install_resource_replay(resources, events):
    """Install exact-URL GET replay in the current disposable test process.

    ``resources`` maps URL to (bytes, expected SHA-256). Validate the entire
    mapping before replacing either function. Return a restoration callback.
    """
    import requests
    import urllib.request

    bodies = {}
    for url, (body, digest) in resources.items():
        if not isinstance(url, str) or not url.startswith('https://'):
            raise ValueError('Resource URL must use HTTPS')
        if not isinstance(body, bytes) or hashlib.sha256(body).hexdigest() != digest:
            raise ValueError('Resource body identity mismatch')
        bodies[url] = body
    if not bodies:
        raise ValueError('Resource replay requires a nonempty allowlist')

    original_urlopen = urllib.request.urlopen
    original_get = requests.get

    def lookup(url, client):
        allowed = isinstance(url, str) and url in bodies
        events.append({'client': client, 'url': str(url), 'allowed': allowed})
        if not allowed:
            raise RuntimeError('Uncached resource requested during offline evaluation')
        return bodies[url]

    def urlopen(url, data=None, timeout=None, **kwargs):
        # A TLS context affects live transport, not cached response bytes.
        # Validate its type, then record that this transport setting is bypassed.
        context = kwargs.pop('context', None)
        if context is not None and not isinstance(context, ssl.SSLContext):
            raise ValueError('Invalid TLS context')
        if data is not None or kwargs:
            raise ValueError('Unsupported urllib request options: ' + ','.join(sorted(kwargs)))
        if isinstance(url, urllib.request.Request):
            if url.get_method() != 'GET' or url.data is not None:
                raise ValueError('Only GET resource reads are supported')
            url = url.full_url
        body = lookup(url, 'urllib')
        events[-1]['tls_context_bypassed'] = context is not None
        headers = Message()
        headers['Content-Type'] = 'text/plain; charset=utf-8'
        headers['Content-Length'] = str(len(body))
        response = addinfourl(io.BytesIO(body), headers, url, 200)
        response.mode = 'rb'
        return response

    def get(url, **kwargs):
        if set(kwargs) - {'timeout'}:
            raise ValueError('Unsupported requests options')
        body = lookup(url, 'requests')
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.encoding = 'utf-8'
        response._content = body
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response

    urllib.request.urlopen = urlopen
    requests.get = get

    def restore():
        urllib.request.urlopen = original_urlopen
        requests.get = original_get

    return restore
