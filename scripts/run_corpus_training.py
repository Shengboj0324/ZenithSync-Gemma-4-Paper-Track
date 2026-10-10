"""Deadline-supervised corpus training; never starts or stops a Runpod Pod."""
from datetime import datetime
import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_corpus_training_worker import parser, WORKER_SOURCES
from scripts.run_p1_training_worker import require_volume
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.corpus_run import preflight_corpus_run
from zenithsync.process_supervisor import run_bounded
from zenithsync.training_schedule import initial_cursor, iter_updates
from zenithsync.session_report import validate_session_report


def main():
    arguments = parser()
    arguments.description = __doc__
    arguments.add_argument('--session-deadline', required=True,
                           help='Authorized absolute ISO-8601 deadline with timezone')
    args = arguments.parse_args()
    deadline = datetime.fromisoformat(args.session_deadline)
    if deadline.tzinfo is None or deadline.utcoffset() is None:
        raise ValueError('Timezone-aware session deadline required')
    corpus, schedule, config = preflight_corpus_run(
        corpus_root=args.corpus,corpus_sha256=args.corpus_sha256,
        schedule_path=args.schedule,schedule_sha256=args.schedule_sha256,
        config_path=args.config,config_sha256=args.config_sha256)
    execution_config = {'config_sha256':args.config_sha256,
        'sources':{name:file_record(ROOT/name) for name in WORKER_SOURCES},
        'versions':{name:version(name) for name in ('torch','transformers','compressed-tensors','peft')},
        'adapter':{'rank':4,'alpha':8,'dropout':0.0},'dtype':'bfloat16','attention':'eager'}
    bindings = {'base_manifest_sha256':args.manifest_sha256,'corpus_manifest_sha256':args.corpus_sha256,
        'corpus_content_sha256':corpus.summary['content_sha256'],'schedule_sha256':schedule['schedule_sha256'],
        'worker_config_sha256':hashlib.sha256(canonical_json(execution_config)).hexdigest()}
    from zenithsync.checkpoint_storage import load_checkpoint
    start_cursor = initial_cursor(schedule)
    supplied = [args.resume is not None,args.resume_sha256 is not None,args.resume_size is not None]
    if any(supplied) and not all(supplied):
        raise ValueError('Resume requires path, SHA-256 and size together')
    if args.resume is not None:
        payload = load_checkpoint(args.resume,expected_identity={'sha256':args.resume_sha256,
            'size_bytes':args.resume_size},max_bytes=config['max_checkpoint_bytes'])
        if payload.get('bindings') != bindings:raise ValueError('Resume artifact bindings differ')
        start_cursor = payload['cursor']
        next(iter_updates(schedule,resume=start_cursor),None)
        del payload
    require_volume(args.output,args.volume_root)
    args.output.mkdir(parents=True,exist_ok=False)
    worker_output = args.output/'worker'
    command = [sys.executable,str(ROOT/'scripts/run_corpus_training_worker.py')]
    for key, value in vars(args).items():
        if key == 'session_deadline' or value is None:continue
        if key == 'output':value = worker_output
        if isinstance(value,Path):value = value.resolve()
        command.extend(['--'+key.replace('_','-'),str(value)])
    lifecycle = run_bounded(command,log_path=args.output/'worker.log',deadline=deadline,
        maximum_seconds=config['max_seconds'],env={**os.environ,'PYTHONUNBUFFERED':'1'},
        stop_path=args.output/'STOP')
    (args.output/'lifecycle.json').write_bytes(canonical_json(lifecycle))
    if not lifecycle['success']:
        raise RuntimeError('Corpus worker failed, exceeded deadline, or left processes running')
    worker = load_json(worker_output/'worker.json')
    if worker.get('status') != 'corpus_session_returned':
        raise ValueError('Worker session receipt missing or invalid')
    if worker['bindings'] != bindings or worker['execution_config'] != execution_config:
        raise ValueError('Worker execution identity differs from supervisor')
    session = worker['session']
    validation = validate_session_report(session,schedule=schedule,start_cursor=start_cursor,
        bindings=bindings,checkpoint_root=(worker_output/'checkpoints').resolve(),
        **{key:config[key] for key in ('max_updates','max_seconds','max_checkpoint_bytes',
                                       'max_session_checkpoint_bytes')},
        load_payload=lambda path,identity:load_checkpoint(path,expected_identity=identity,
                                                         max_bytes=config['max_checkpoint_bytes']))
    (args.output/'receipt.json').write_bytes(canonical_json({
        'schema_version':1,'status':'bounded_corpus_session_returned',
        'worker':file_record(worker_output/'worker.json'),
        'lifecycle':file_record(args.output/'lifecycle.json'),
        'committed_updates':len(session['checkpoints']),'stop_reason':session['status'],
        'validation':validation,
        'scope':'Bounded execution and checkpoint file identities; no held-out performance claim'}))
    print('Corpus worker returned with verified checkpoint files; Pod billing state unchanged')


if __name__ == '__main__':main()
