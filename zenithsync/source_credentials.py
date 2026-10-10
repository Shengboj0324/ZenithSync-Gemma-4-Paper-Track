"""Conservative source-text credential indicators, never credential validation.

Reports contain only rule names and character locations. Absence of indicators
is not proof of absence of secrets; flagged examples require review, not silent
redaction that would break trajectory provenance.
"""
import re

_RULES = (
    ('private_key_header', re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')),
    ('aws_access_key_id', re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('github_token', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b')),
    ('authorization_literal', re.compile(
        r'''(?ix)\b(?:proxy-)?authorization\b["']?\s*[:=]\s*["']?
        (?:bearer\s+|basic\s+)?(?P<value>[A-Za-z0-9_./+~=-]{20,})''')),
)


def scan_text(text):
    """Return deterministic non-secret diagnostics; offsets are Unicode characters."""
    if not isinstance(text, str):
        raise TypeError('Source text must be a string')
    findings = []
    for rule, pattern in _RULES:
        for match in pattern.finditer(text):
            start, end = match.span('value') if 'value' in pattern.groupindex else match.span()
            findings.append({'rule': rule, 'start': start, 'end': end,
                             'line': text.count('\n', 0, start) + 1})
    return sorted(findings, key=lambda row: (row['start'], row['end'], row['rule']))


def require_no_credential_indicators(value):
    """Reject indicators anywhere in a decoded source message tree before replay.

    Dictionary authorization fields are scanned together with their values.
    Errors deliberately omit values, field names and snippets. This is a narrow
    indicator gate, not a general secret detector or training admission gate.
    """
    pending = [value]
    visited = set()
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if scan_text(current):
                raise ValueError('Source credential indicator requires review before replay')
        elif isinstance(current, (dict, list)):
            identity = id(current)
            if identity in visited:
                continue
            visited.add(identity)
            if isinstance(current, dict):
                for key, item in current.items():
                    if isinstance(key, str) and key.casefold() in ('authorization', 'proxy-authorization'):
                        if isinstance(item, str) and scan_text('Authorization: ' + item):
                            raise ValueError('Source credential indicator requires review before replay')
                    pending.extend((key, item))
            else:
                pending.extend(current)
