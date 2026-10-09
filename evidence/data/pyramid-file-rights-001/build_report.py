"""Reconcile this recorded replay's direct reads against its pinned source files.

Shell classifications below are manual observations of this exact event digest,
not a general shell parser or automatic license approval.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json

out = Path(__file__).resolve().parent
attempt = ROOT / 'evidence/data/pyramid-budget-replay-001'
events_path = attempt / 'events.json'
identity = file_record(events_path)
if identity['sha256'] != 'f7812a354d8282de593853a791932990010d1408f34acdf78a727e514147e532':
    raise ValueError('Manual classification applies only to the reviewed replay')
events = load_json(events_path)
calls = {e['source_index']: e['native_calls'][0] for e in events if e['native_calls']}
source = out / 'snapshot/source'
for index, name in [(18, 'src/pyramid/settings.py'), (20, 'tests/test_settings.py')]:
    if calls[index]['result']['content'] != (source / name).read_text().removesuffix('\n'):
        raise ValueError('Recorded initial read differs from pinned source')
readme = ''.join((source / 'README.rst').read_text().splitlines(keepends=True)[:50])
if calls[8]['result']['content'] != readme.removesuffix('\n'):
    raise ValueError('README range differs from pinned source')
edit = calls[32]['arguments']
settings = (source / 'src/pyramid/settings.py').read_text()
if settings.count(edit['old_string']) != 1:
    raise ValueError('Expected a unique edit location')
if settings.replace(edit['old_string'], edit['new_string']).removesuffix('\n') != calls[56]['result']['content']:
    raise ValueError('Final read does not match the captured edit')
# Every shell observation is explicitly accounted for, including errors and truncation.
groups = {
    'path_names_or_directory_metadata': [4, 6, 12, 16, 24],
    'runtime_version': [14],
    'empty_grep_error': [22],
    'teacher_script_or_inline_execution': [28, 34, 38, 40, 44, 48, 52, 60],
    'pytest_output': [46, 54, 62],
    'empty_cleanup_output': [58],
}
classified = [i for indices in groups.values() for i in indices]
actual = [i for i, c in calls.items() if c['name'] == 'run_command']
if len(classified) != len(set(classified)) or set(classified) != set(actual):
    raise ValueError('Shell classification incomplete or duplicated')
report = {
    'schema_version': 1,
    'events': identity,
    'snapshot_files': load_json(out / 'snapshot/files.json'),
    'snapshot': file_record(out / 'snapshot/snapshot.json'),
    'comparison_normalization': 'Remove exactly one terminal LF from snapshot text to match native read_file serialization.',
    'source_read_comparisons': {'README_first_50_lines': True, 'initial_settings': True,
                                'initial_tests': True, 'settings_after_edit': True},
    'shell_observation_classes': groups,
    'source_notices': {name: file_record(ROOT / 'evidence/data/pyramid-notices-001/notices' / name)
                       for name in ['LICENSE.txt', 'COPYRIGHT.txt', 'docs/copyright.rst']},
    'patch': file_record(attempt / 'submitted.patch'),
    'findings': [
        'Three directly read existing source files; run_tests.sh read failed.',
        'The inspected source files contain no ZPL header or stolen-from-Paste marker.',
        'Root README explicitly identifies the Repoze Public License outside its observed first 50 lines.',
        'No rendered docs body was observed in the reviewed native tool results; directory listings include docs paths.',
        'Event 62 includes warnings with snippets from asset.py and installed pkg_resources; these were not part of the three direct-read files.',
        'Events 54 and 62 contain visibly cut-off pytest output; no reconstruction of omitted bytes is claimed.',
        'Event 38 reports a failed teacher-authored test despite exit code zero; process success is not test success.',
        'The saved source patch contains no prominent modification/date notice. Preserve raw evidence; derived redistribution needs a separate compliant packaging decision.',
    ],
    'training_approved': False,
    'remaining': ['Dependency warning snippet notices and issue provenance',
                  'Derived distribution attribution and modification notices',
                  'Dataset-wide semantic isolation and corpus admission'],
    'scope': 'This native replay only; original teacher observations, all dependency files, and all source history are not audited.',
    'script': file_record(Path(__file__)),
    'export_probe': file_record(out / 'export_probe.py'),
}
if file_record(events_path) != identity:
    raise ValueError('Events changed during audit')
(out / 'report.json').write_bytes(canonical_json(report))
print({'direct_source_files_verified': 3, 'shell_observations_classified': len(actual), 'training_approved': False})
