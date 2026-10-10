"""CPU-only admission and configuration checks for the full-model corpus worker."""
import math
from pathlib import Path

from .artifacts import file_record, load_json
from .training_corpus import IndexedCorpus
from .training_schedule import iter_updates


def preflight_corpus_run(*, corpus_root: Path, corpus_sha256, schedule_path: Path,
                        schedule_sha256, config_path: Path, config_sha256):
    config_identity = file_record(config_path)
    schedule_identity = file_record(schedule_path)
    if config_identity['sha256'] != config_sha256 or schedule_identity['sha256'] != schedule_sha256:
        raise ValueError('Worker config or schedule file identity mismatch')
    if config_identity['size_bytes'] > 65536 or schedule_identity['size_bytes'] > 16*1024**2:
        raise ValueError('Oversized config or schedule')
    config, schedule = load_json(config_path), load_json(schedule_path)
    integers = {'seed', 'max_updates', 'max_seconds', 'max_sequence_tokens',
                'max_checkpoint_bytes', 'max_session_checkpoint_bytes',
                'max_corpus_bytes', 'max_example_bytes'}
    if not isinstance(config, dict) or set(config) != integers | {'schema_version', 'learning_rate'}:
        raise ValueError('Exact corpus worker config fields required')
    if type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise ValueError('Unsupported corpus worker config')
    for name in integers:
        minimum = 0 if name == 'seed' else 1
        if type(config[name]) is not int or config[name] < minimum:
            raise ValueError('Invalid config integer: ' + name)
    rate = config['learning_rate']
    if config['seed'] >= 2**32:
        raise ValueError('Seed must fit the NumPy uint32 seed range')
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
        raise ValueError('Positive finite learning rate required')
    if (config['max_sequence_tokens'] < 2
            or config['max_session_checkpoint_bytes'] < config['max_checkpoint_bytes']):
        raise ValueError('Invalid sequence or checkpoint capacity')
    next(iter_updates(schedule), None)
    corpus = IndexedCorpus(corpus_root, corpus_root/'corpus.json',
        expected_manifest_sha256=corpus_sha256, purpose='training',
        max_total_bytes=config['max_corpus_bytes'], max_example_bytes=config['max_example_bytes'])
    summary = corpus.summary
    if schedule['corpus_content_sha256'] != summary['content_sha256']:
        raise ValueError('Schedule belongs to another corpus')
    metadata = [{key: row[key] for key in ('example_id', 'input_tokens', 'supervised_tokens')}
                for row in corpus.metadata()]
    if sorted(metadata, key=lambda row: row['example_id']) != schedule['examples']:
        raise ValueError('Schedule does not cover the admitted training split exactly')
    if any(row['input_tokens'] > config['max_sequence_tokens'] for row in metadata):
        raise ValueError('Corpus exceeds configured sequence capacity')
    if file_record(config_path) != config_identity or file_record(schedule_path) != schedule_identity:
        raise ValueError('Config or schedule changed during preflight')
    return corpus, schedule, config
