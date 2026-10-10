"""Exact public UTF-8 response replay for disposable, offline test processes.

This supports successful body reads through requests Sessions, not arbitrary
HTTP behavior. It does not reproduce TLS, cookies, redirects, hooks or timing.
Install only in an isolated process; restoration is not concurrency-safe.
"""
import hashlib
import math
from urllib.parse import urlsplit


def install_session_resource_replay(resources, events):
    """Validate all records before replacing Session.send; return its restorer.

    Each exact prepared URL maps to body bytes, sha256 and content_type fields.
    Recorded responses are public, status 200 and decoded as UTF-8. Callers must
    independently qualify provenance, rights and the adequacy of this model.
    """
    import requests

    if not isinstance(resources, dict) or not resources or not isinstance(events, list):
        raise ValueError('Nonempty resource mapping and event list required')
    validated = {}
    for url, record in resources.items():
        if not isinstance(url, str):
            raise ValueError('Resource URL must be text')
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment
                or any(c.isspace() or ord(c) < 32 for c in url)):
            raise ValueError('Expected an exact public HTTPS URL without fragment')
        if not isinstance(record, dict) or set(record) != {'body', 'sha256', 'content_type'}:
            raise ValueError('Exact response record fields required')
        body, digest, content_type = record['body'], record['sha256'], record['content_type']
        if not isinstance(body, bytes) or hashlib.sha256(body).hexdigest() != digest:
            raise ValueError('Response body identity mismatch')
        if (not isinstance(content_type, str) or not content_type.strip()
                or any(ord(c) < 32 or ord(c) == 127 for c in content_type)):
            raise ValueError('Invalid recorded content type')
        validated[url] = (body, content_type)

    original = requests.sessions.Session.send

    def send(session, request, **kwargs):
        reason = None
        if request.method != 'GET' or request.body is not None:
            reason = 'Only body-free GET requests supported'
        elif any(name in request.headers for name in
                 ('Authorization', 'Proxy-Authorization', 'Cookie', 'Range',
                  'If-Match', 'If-None-Match', 'If-Modified-Since', 'If-Unmodified-Since')):
            reason = 'Authenticated or conditional requests are unsupported'
        elif any(request.hooks.values()):
            reason = 'Response hooks are unsupported'
        elif set(kwargs) - {'timeout', 'verify', 'cert', 'proxies', 'stream', 'allow_redirects'}:
            reason = 'Unknown transport options'
        elif (kwargs.get('verify', True) is not True or kwargs.get('cert') is not None
              or kwargs.get('proxies') or kwargs.get('stream', False) is not False
              or type(kwargs.get('allow_redirects', True)) is not bool):
            reason = 'Unsupported transport configuration'
        else:
            timeout = kwargs.get('timeout')
            values = timeout if isinstance(timeout, tuple) else (timeout,)
            if ((isinstance(timeout, tuple) and len(timeout) != 2)
                    or any(v is not None and (type(v) not in (int, float)
                           or not math.isfinite(v) or v <= 0) for v in values)):
                reason = 'Invalid transport timeout'
        if reason is None and request.url not in validated:
            reason = 'Unrecorded prepared URL'
        events.append({'url': request.url, 'method': request.method,
                       'allowed': reason is None, 'reason': reason,
                       'live_transport_executed': False})
        if reason is not None:
            raise ValueError(reason)
        body, content_type = validated[request.url]
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response.encoding = 'utf-8'
        response.headers['Content-Type'] = content_type
        response._content = body
        response._content_consumed = True
        return response

    requests.sessions.Session.send = send

    def restore():
        requests.sessions.Session.send = original

    return restore
