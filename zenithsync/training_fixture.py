"""Native-tokenized qualification input, explicitly separate from training data."""

from zenithsync.artifacts import file_record
from zenithsync.training_batch import collate_training_examples
from zenithsync.training_masks import assistant_training_tokens


def prepare_pilot_batch(model_path, manifest, *, max_length=64):
    from transformers import AutoTokenizer

    for filename in ['chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json']:
        expected = next(row for row in manifest['files'] if row['path'] == filename)
        if file_record(model_path / filename) != {key: expected[key] for key in ['sha256', 'size_bytes']}:
            raise ValueError('Tokenizer file identity mismatch: ' + filename)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    messages = [{'role': 'user', 'content': 'Return the Python expression for adding x and y.'},
                {'role': 'assistant', 'content': 'x + y'}]
    encoded = assistant_training_tokens(tokenizer, messages,
        template_sha256=file_record(model_path / 'chat_template.jinja')['sha256'], allowed_tools=set())
    selected = [token for token in encoded['labels'] if token != -100]
    if tokenizer.decode(selected, skip_special_tokens=False) != 'x + y<turn|>\n':
        raise ValueError('Qualification supervision differs from independent expected text')
    batch = collate_training_examples([encoded], pad_token_id=tokenizer.pad_token_id,
                                     vocab_size=len(tokenizer), max_length=max_length)
    return {'schema_version': 1, 'scope': 'Synthetic qualification fixture; not a training corpus',
            'messages': messages, 'encoded': encoded, **batch}
