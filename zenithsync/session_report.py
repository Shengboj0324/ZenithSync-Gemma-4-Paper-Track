"""Independent schedule/accounting verification of a completed worker report.

This establishes checkpoint and schedule consistency, not numerical training
quality. The caller supplies an independently hash-bound checkpoint reader.
"""
import math
from pathlib import Path

from .artifacts import canonical_json, file_record
from .training_schedule import iter_updates


def validate_session_report(report, *, schedule, start_cursor, bindings, checkpoint_root,
                            max_updates, max_seconds, max_checkpoint_bytes,
                            max_session_checkpoint_bytes, load_payload):
    fields = {'status','cursor','checkpoints','checkpoint_bytes','elapsed_seconds'}
    if not isinstance(report, dict) or set(report) != fields:
        raise ValueError('Invalid session report schema')
    for value in (max_updates,max_seconds,max_checkpoint_bytes,max_session_checkpoint_bytes):
        if type(value) is not int or value <= 0:
            raise ValueError('Positive verification budget required')
    elapsed = report['elapsed_seconds']
    if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError('Invalid elapsed time')
    records = report['checkpoints']
    if not isinstance(records,list) or len(records) > max_updates:
        raise ValueError('Checkpoint count exceeds update budget')
    root = Path(checkpoint_root)
    if not root.is_dir() or any(p.is_symlink() for p in [root,*root.parents]):
        raise ValueError('Ordinary checkpoint directory required')
    root = root.resolve(strict=True)
    updates = iter_updates(schedule,resume=start_cursor)
    pending = next(updates,None)
    cursor = start_cursor
    stored = 0
    for record in records:
        if not isinstance(record,dict) or set(record) != {'path','identity','cursor','metrics'}:
            raise ValueError('Invalid checkpoint record')
        if pending is None or canonical_json(record['cursor']) != canonical_json(pending['next_cursor']):
            raise ValueError('Checkpoint cursor skips or repeats scheduled work')
        path = Path(record['path'])
        expected_path = root/('update-'+str(pending['step']).zfill(8)+'.pt')
        if path != expected_path or path.is_symlink():
            raise ValueError('Checkpoint path differs from scheduled update')
        identity = file_record(path)
        if identity != record['identity'] or not 0 < identity['size_bytes'] <= max_checkpoint_bytes:
            raise ValueError('Checkpoint identity or size differs')
        if max_session_checkpoint_bytes-stored < max_checkpoint_bytes:
            raise ValueError('Checkpoint was written without required byte reservation')
        stored += identity['size_bytes']
        metrics = record['metrics']
        expected_counts = [row['supervised_tokens'] for row in pending['examples']]
        if (not isinstance(metrics,dict) or set(metrics) != {
                'supervised_tokens','microbatch_supervised_tokens','token_mean_loss','microbatches'}
                or type(metrics['supervised_tokens']) is not int
                or metrics['supervised_tokens'] != pending['supervised_tokens']
                or type(metrics['microbatches']) is not int
                or metrics['microbatches'] != len(expected_counts)
                or not isinstance(metrics['microbatch_supervised_tokens'],list)
                or any(type(value) is not int for value in metrics['microbatch_supervised_tokens'])
                or metrics['microbatch_supervised_tokens'] != expected_counts
                or type(metrics['token_mean_loss']) not in (int,float)
                or not math.isfinite(metrics['token_mean_loss']) or metrics['token_mean_loss'] < 0):
            raise ValueError('Training metrics disagree with scheduled token counts')
        payload = load_payload(path,identity)
        if (not isinstance(payload,dict) or payload.get('bindings') != bindings
                or canonical_json(payload.get('cursor')) != canonical_json(record['cursor'])
                or not isinstance(payload.get('optimizer'),dict)
                or type(payload['optimizer'].get('completed_steps')) is not int
                or payload['optimizer']['completed_steps'] != pending['step']):
            raise ValueError('Checkpoint payload differs from session report')
        del payload
        cursor = pending['next_cursor']
        pending = next(updates,None)
    if (canonical_json(report['cursor']) != canonical_json(cursor) or type(report['checkpoint_bytes']) is not int
            or report['checkpoint_bytes'] != stored):
        raise ValueError('Final cursor or byte accounting differs')
    reason = report['status']
    valid_reason = (
        (reason == 'schedule_complete' and pending is None)
        or (reason == 'update_budget' and pending is not None and len(records) == max_updates)
        or (reason == 'wall_budget' and pending is not None and elapsed >= max_seconds)
        or (reason == 'checkpoint_budget' and pending is not None
            and max_session_checkpoint_bytes-stored < max_checkpoint_bytes))
    if not valid_reason:
        raise ValueError('Claimed stop reason is not supported by the report')
    return {'verified_updates':len(records),'checkpoint_bytes':stored,'stop_reason':reason}
