"""Single-process corpus training with explicit budgets and durable update boundaries.

The caller constructs and verifies the model/runtime and uses an external hard
deadline supervisor. This loop's wall limit is checked only between updates.
"""
import time
from pathlib import Path

from .adapter_checkpoint import (capture_adapter_checkpoint, restore_adapter_checkpoint,
                                 validate_checkpoint_bindings)
from .checkpoint_storage import load_checkpoint, save_checkpoint
from .corpus_training import train_corpus_update
from .training_corpus import IndexedCorpus
from .training_schedule import initial_cursor, iter_updates
from .training_state import require_identical_state
from .adapter_checkpoint import frozen_state


def run_training_session(model, optimizer, *, corpus, schedule, bindings, expected_frozen,
                         output: Path, max_updates, max_seconds, max_sequence_tokens,
                         max_checkpoint_bytes, max_session_checkpoint_bytes, resume=None):
    """Checkpoint every successful update; resume only a supplied hash-bound file.

    Failures propagate: callers must discard mutable training state. Checkpoints
    from preceding updates remain recoverable. No automatic directory scan or
    inferred latest checkpoint is accepted.
    """
    for name, value in [('max_updates', max_updates), ('max_seconds', max_seconds),
                        ('max_sequence_tokens', max_sequence_tokens),
                        ('max_checkpoint_bytes', max_checkpoint_bytes),
                        ('max_session_checkpoint_bytes', max_session_checkpoint_bytes)]:
        if type(value) is not int or value <= 0:
            raise ValueError(name + ' must be a positive integer')
    if max_sequence_tokens < 2 or max_session_checkpoint_bytes < max_checkpoint_bytes:
        raise ValueError('Invalid sequence or checkpoint budget')
    validate_checkpoint_bindings(bindings, schedule)
    next(iter_updates(schedule), None)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if any(parent.is_symlink() for parent in output.parents):
        raise ValueError('Symlinked checkpoint directory ancestry rejected')
    if not isinstance(corpus, IndexedCorpus):
        raise ValueError('Validated indexed corpus required')
    summary = corpus.summary
    if summary['purpose'] != 'training' or not summary['training_admitted']:
        raise ValueError('Training-purpose admitted corpus required')
    if (bindings['corpus_manifest_sha256'] != summary['manifest']['sha256']
            or bindings['corpus_content_sha256'] != summary['content_sha256']
            or bindings['schedule_sha256'] != schedule['schedule_sha256']):
        raise ValueError('Session bindings differ from verified corpus or schedule')
    metadata = [{key: row[key] for key in ('example_id', 'input_tokens', 'supervised_tokens')}
                for row in corpus.metadata()]
    if sorted(metadata, key=lambda row: row['example_id']) != schedule['examples']:
        raise ValueError('Schedule must cover exactly the admitted training examples')
    if any(row['input_tokens'] > max_sequence_tokens for row in metadata):
        raise ValueError('Corpus exceeds configured sequence capacity')
    require_identical_state(expected_frozen, frozen_state(model))
    started = time.monotonic()
    cursor = initial_cursor(schedule)
    if resume is not None:
        if not isinstance(resume, dict) or set(resume) != {'path', 'identity'}:
            raise ValueError('Explicit checkpoint path and identity required')
        payload = load_checkpoint(Path(resume['path']), expected_identity=resume['identity'],
                                  max_bytes=max_checkpoint_bytes)
        cursor = restore_adapter_checkpoint(model, optimizer, payload, bindings=bindings,
                                            schedule=schedule, expected_frozen=expected_frozen)
        del payload
    elif optimizer.state:
        raise ValueError('New session requires an optimizer with no existing state')
    updates = iter_updates(schedule, resume=cursor)
    # Force schedule validation before creating output or executing training.
    pending = next(updates, None)
    output.mkdir(parents=True, exist_ok=False)
    checkpoints = []
    stored_bytes = 0
    reason = 'schedule_complete'
    while pending is not None:
        if len(checkpoints) >= max_updates:
            reason = 'update_budget'; break
        if time.monotonic() - started >= max_seconds:
            reason = 'wall_budget'; break
        # Reserve the full per-checkpoint cap before spending an optimizer step.
        if max_session_checkpoint_bytes - stored_bytes < max_checkpoint_bytes:
            reason = 'checkpoint_budget'; break
        metrics = train_corpus_update(model, optimizer, corpus, pending,
                                      max_sequence_tokens=max_sequence_tokens)
        payload = capture_adapter_checkpoint(model, optimizer, bindings=bindings,
            schedule=schedule, cursor=pending['next_cursor'], expected_frozen=expected_frozen)
        path = output / ('update-' + str(pending['step']).zfill(8) + '.pt')
        identity = save_checkpoint(path, payload, max_bytes=max_checkpoint_bytes)
        del payload
        # Advance the committed cursor only after checkpoint publication returns.
        cursor = dict(pending['next_cursor'])
        stored_bytes += identity['size_bytes']
        checkpoints.append({'path': str(path.resolve()), 'identity': identity,
                            'cursor': cursor, 'metrics': metrics})
        pending = next(updates, None)
    return {'status': reason, 'cursor': cursor, 'checkpoints': checkpoints,
            'checkpoint_bytes': stored_bytes, 'elapsed_seconds': time.monotonic() - started}
