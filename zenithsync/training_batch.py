"""Validated right-padding for independently masked causal training examples.

No truncation or concatenation: examples remain separate attention sequences.
Loss normalization counts supervised next-token targets, not padded positions.
"""


def collate_training_examples(examples, *, pad_token_id, vocab_size, max_length):
    for name, value in [('vocab_size', vocab_size), ('max_length', max_length)]:
        if type(value) is not int or value <= 0:
            raise ValueError(name + ' must be a positive integer')
    if type(pad_token_id) is not int or not 0 <= pad_token_id < vocab_size:
        raise ValueError('Invalid padding token')
    if not isinstance(examples, list) or not examples:
        raise ValueError('A nonempty batch is required')
    rows = []
    counts = []
    for example in examples:
        if not isinstance(example, dict):
            raise ValueError('Training example must be a mapping')
        ids, labels = example.get('input_ids'), example.get('labels')
        if not isinstance(ids, list) or not isinstance(labels, list) or len(ids) != len(labels):
            raise ValueError('Token and label lengths must agree')
        if not 2 <= len(ids) <= max_length:
            raise ValueError('Example length out of bounds; silent truncation is forbidden')
        if any(type(token) is not int or not 0 <= token < vocab_size for token in ids):
            raise ValueError('Invalid input token')
        if any(type(label) is not int or label not in (-100, token)
               for token, label in zip(ids, labels, strict=True)):
            raise ValueError('Labels must copy input tokens or use the ignore index')
        if labels[0] != -100:
            raise ValueError('First position has no predecessor for causal supervision')
        count = sum(label != -100 for label in labels[1:])
        if not count:
            raise ValueError('Every example must contain a supervised next-token target')
        counts.append(count)
        rows.append((ids, labels))
    width = max(len(ids) for ids, _ in rows)
    batch = {'input_ids': [], 'labels': [], 'attention_mask': []}
    for ids, labels in rows:
        padding = width - len(ids)
        batch['input_ids'].append(ids + [pad_token_id] * padding)
        batch['labels'].append(labels + [-100] * padding)
        batch['attention_mask'].append([1] * len(ids) + [0] * padding)
    return {'batch': batch, 'supervised_tokens': sum(counts), 'per_example_supervised_tokens': counts}
