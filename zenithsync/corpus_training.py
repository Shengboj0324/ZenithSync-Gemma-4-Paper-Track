"""Bridge admitted indexed examples to one-example-at-a-time optimizer updates."""

from .corpus_optimization import streamed_token_weighted_step
from .training_batch import collate_training_examples
from .training_corpus import IndexedCorpus


def train_corpus_update(model, optimizer, corpus, update, *, max_sequence_tokens):
    """Execute one scheduled update without retaining all example tensors.

    The caller owns schedule/cursor validation, checkpoint publication and RNG
    recovery. This function never advances a durable cursor on its own.
    """
    import torch

    if not isinstance(corpus, IndexedCorpus):
        raise ValueError('Validated indexed corpus required')
    summary = corpus.summary
    if summary['purpose'] != 'training' or not summary['training_admitted']:
        raise ValueError('Training-purpose admitted corpus required')
    if type(max_sequence_tokens) is not int or max_sequence_tokens < 2:
        raise ValueError('Positive sequence capacity of at least two required')
    rows = update.get('examples')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Nonempty scheduled examples required')
    seen = set()
    expected_input = expected_targets = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'example_id', 'input_tokens', 'supervised_tokens'}:
            raise ValueError('Exact scheduled example fields required')
        name = row['example_id']
        if not isinstance(name, str) or name in seen:
            raise ValueError('Unique scheduled example IDs required')
        seen.add(name)
        metadata = corpus.example_metadata(name)
        if metadata['split'] != 'train':
            raise ValueError('Non-training example in update')
        for key in ('input_tokens', 'supervised_tokens'):
            if type(row[key]) is not int or row[key] != metadata[key]:
                raise ValueError('Scheduled counts differ from validated corpus')
        if row['input_tokens'] > max_sequence_tokens:
            raise ValueError('Example exceeds sequence capacity; truncation forbidden')
        expected_input += row['input_tokens']
        expected_targets += row['supervised_tokens']
    for key, expected in [('input_tokens', expected_input), ('supervised_tokens', expected_targets)]:
        if type(update.get(key)) is not int or update[key] != expected:
            raise ValueError('Update total differs from corpus counts')
    devices = {parameter.device for parameter in model.parameters()}
    if len(devices) != 1:
        raise ValueError('Single-device model required')
    device = next(iter(devices))

    def batches():
        for row in rows:
            example = corpus.fetch(row['example_id'])
            collated = collate_training_examples(
                [example], pad_token_id=corpus.pad_token_id,
                vocab_size=corpus.vocab_size, max_length=max_sequence_tokens)
            tensors = {key: torch.tensor(value, dtype=torch.long, device=device)
                       for key, value in collated['batch'].items()}
            del example, collated
            yield tensors
            # Release this batch before fetching or allocating the next one.
            del tensors

    return streamed_token_weighted_step(
        model, optimizer, batches(), expected_supervised_tokens=expected_targets)
