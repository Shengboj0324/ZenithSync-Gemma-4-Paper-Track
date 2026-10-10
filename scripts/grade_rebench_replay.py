"""Grade an exact replay patch against qualified, profile-bound snapshot controls."""
import argparse
import base64
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.pytest_controls import compare_controls, compare_candidate
from scripts.run_rebench_controls import validate_profile
from scripts.qualify_swe_rebench_evaluator import PROBE, PLUGIN
from scripts.compare_source_snapshot import run_image


def source_allowlist(paths):
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('Unique explicit candidate source paths required')
    for path in paths:
        pure = PurePosixPath(path)
        if (not path or path == '.' or pure.is_absolute() or str(pure) != path
                or any(p in ('.', '..', '.git') for p in pure.parts) or '\x00' in path):
            raise ValueError('Invalid candidate source path')
    return paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt', type=Path, required=True)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--allow-source', action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    allowed = source_allowlist(args.allow_source)
    paths = [args.attempt/'receipt.json', args.attempt/'submitted.patch',
             args.controls/'comparison.json', args.controls/'report.json',
             args.inputs/'receipt.json', args.inputs/'metadata.json', args.inputs/'tests.patch',
             args.profile, args.snapshot/'snapshot.json', args.snapshot/'receipt.json',
             args.snapshot/'verification.json', args.snapshot/'input-bindings.json',
             Path(__file__), ROOT/'scripts/qualify_swe_rebench_evaluator.py',
             ROOT/'zenithsync/pytest_controls.py', ROOT/'scripts/compare_source_snapshot.py',
             ROOT/'scripts/run_rebench_controls.py']
    paths += [args.controls/role/name for role in ('base','reference')
              for name in ('outcomes.json','runtime.json','receipt.json')]
    identities = {str(path):file_record(path) for path in paths}
    comparison = load_json(args.controls/'comparison.json')
    for path, identity in comparison['inputs'].items():
        if file_record(Path(path)) != identity:
            raise ValueError('Qualified control comparison input drift')
        identities[path] = identity
    controls = load_json(args.controls/'report.json')
    # Execution profile, tests, source metadata and verified snapshot must be
    # byte-identical to the inputs used for the qualified paired controls.
    for path in [args.inputs/'receipt.json', args.inputs/'metadata.json', args.inputs/'tests.patch',
                 args.profile, *[args.snapshot/name for name in
                    ('snapshot.json','receipt.json','verification.json','input-bindings.json')]]:
        if controls['inputs'].get(str(path)) != identities[str(path)]:
            raise ValueError('Candidate configuration differs from qualified controls: '+str(path))
    template = ROOT/'scripts/qualify_swe_rebench_evaluator.py'
    if controls['inputs'].get(str(template)) != identities[str(template)]:
        raise ValueError('Control probe changed since qualification')
    metadata = load_json(args.inputs/'metadata.json')
    expectations = {key:metadata[key] for key in ('FAIL_TO_PASS','FAIL_TO_FAIL','PASS_TO_PASS','PASS_TO_FAIL')}
    reference = load_json(args.controls/'reference/outcomes.json')
    compare_controls(load_json(args.controls/'base/outcomes.json'),reference,expectations)
    for role in ('base','reference'):
        r=load_json(args.controls/role/'receipt.json'); runtime=load_json(args.controls/role/'runtime.json')
        if (any(r[key]!=0 for key in ('returncode','copy_returncode','cleanup_returncode'))
                or r['state']['OOMKilled'] or 'error' in runtime
                or runtime.get('tracked_diff_unchanged_by_tests') is not True):
            raise ValueError('Invalid qualified control runtime')
    replay=load_json(args.attempt/'receipt.json')
    profile=validate_profile(load_json(args.profile))
    snapshot=load_json(args.snapshot/'snapshot.json')
    snapshot_run=load_json(args.snapshot/'receipt.json')
    task=load_json(args.inputs/'receipt.json')['task']
    patch=identities[str(args.attempt/'submitted.patch')]
    if (replay['status']!='replayed_not_graded' or replay['cleanup']['removed'] is not True
            or replay['patch']!=patch or patch['size_bytes']>2*1024**2
            or replay['instance_id']!=task['instance_id'] or profile['instance_id']!=task['instance_id']
            or replay['profile']['repo']!=task['repo']
            or replay['profile']['base_commit']!=task['base_commit']
            or snapshot['base_commit']!=task['base_commit']
            or replay['image']!=snapshot_run['image_id']):
        raise ValueError('Replay, task, snapshot or patch mismatch')
    image=snapshot_run['image_id']
    if any(controls['controls'][role]['container']['image_id']!=image for role in ('base','reference')):
        raise ValueError('Control image mismatch')
    patches={'candidate':base64.b64encode((args.attempt/'submitted.patch').read_bytes()).decode(),
             'tests':base64.b64encode((args.inputs/'tests.patch').read_bytes()).decode()}
    settings={'BASE':snapshot['snapshot_commit'],'TREE':snapshot['source_tree'],'ROLE':'candidate',
              'PYTHON':profile['python'],'MODULE':profile['module'],'EXPECTED_ORIGIN':profile['expected_origin'],
              'ALLOWED_PATHS':allowed,'TEST_TARGETS':profile['test_targets'],'PATCHES':patches,
              'PLUGIN':PLUGIN,'RESOURCE_PAYLOAD':'','RESOURCE_ADAPTER':''}
    probe=''.join(f'{key}={value!r}\n' for key,value in settings.items())+PROBE
    args.output.mkdir(parents=True,exist_ok=False)
    result=run_image(image,args.output/'candidate',probe=probe,generated_grading_tests=True)
    runtime=load_json(args.output/'candidate/runtime.json')
    if (any(result[key]!=0 for key in ('returncode','copy_returncode','cleanup_returncode'))
            or result['state']['OOMKilled'] or 'error' in runtime
            or runtime.get('tracked_diff_unchanged_by_tests') is not True):
        raise ValueError('Candidate runtime invalid; retained evidence is not a repair score')
    grade=compare_candidate(reference,load_json(args.output/'candidate/outcomes.json'))
    if any(file_record(Path(path))!=identity for path,identity in identities.items()):
        raise ValueError('Input changed during grading')
    report={'backend':'swe_rebench_full_nodeid_reference','task':task['instance_id'],
            'attempt':identities[str(args.attempt/'receipt.json')],'inputs':{'patch':patch,'bindings':identities},
            'grading':grade,'allowed_source_paths':allowed,'training_approved':False,'model_executed':False,
            'outcomes':file_record(args.output/'candidate/outcomes.json')}
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({'cases':grade['case_count'],'matches':grade['all_cases_match_reference'],
           'disagreements':len(grade['disagreements'])})


if __name__=='__main__':
    main()
