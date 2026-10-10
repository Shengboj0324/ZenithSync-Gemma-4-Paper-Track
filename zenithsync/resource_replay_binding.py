"""Verify a recorded Session environment without approving its training use."""
import hashlib
from pathlib import Path

from .artifacts import file_record
from .session_resource_bundle import DIRECTORY, STARTUP, load_session_resource_bundle


def verify_resource_replay_binding(attempt, profile, bundle=None):
    """Return an explicit environment proof and the files the caller must bind."""
    if bundle is None:
        if (attempt.get('injected_support_modules') is not False
                or attempt.get('session_resources') is not None
                or 'session_resources' in profile):
            raise ValueError('Injected resource replay requires its exact bundle')
        return None, {}
    review = profile.get('session_resources')
    if (not isinstance(review, dict) or set(review) != {'receipt', 'max_bytes'}
            or attempt.get('injected_support_modules') is not True):
        raise ValueError('Explicit reviewed resource environment required')
    _, binding = load_session_resource_bundle(bundle, max_bytes=review['max_bytes'])
    if binding['files']['receipt.json'] != review['receipt']:
        raise ValueError('Resource receipt differs from reviewed profile')
    module_root = Path(__file__).resolve().parent
    implementation_files = [module_root/'session_resource_replay.py',
                            module_root/'session_resource_bundle.py']
    implementations = {str(path): file_record(path) for path in implementation_files}
    for path in implementation_files:
        if attempt.get('sources', {}).get('zenithsync/'+path.name) != implementations[str(path)]:
            raise ValueError('Replay resource implementation differs from verifier')
    expected = {'bundle': binding,
                'adapter': implementations[str(implementation_files[0])],
                'directory': DIRECTORY,
                'startup_sha256': hashlib.sha256(STARTUP.encode('utf-8')).hexdigest()}
    if (attempt.get('session_resources') != expected
            or attempt.get('environment', {}).get('PYTHONPATH') != DIRECTORY):
        raise ValueError('Replay resource staging or startup binding mismatch')
    files = {str(bundle/name): identity for name, identity in binding['files'].items()}
    files.update(implementations)
    files[str(Path(__file__).resolve())] = file_record(Path(__file__).resolve())
    return {'type': 'captured_public_session_responses', 'staging': expected,
            'training_approved': False,
            'scope': 'Byte and configuration binding only; no rights or semantic approval.'}, files
