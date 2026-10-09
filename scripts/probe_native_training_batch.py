"""Check native token masks, padding and weighted microbatch gradients on Gemma.

Random reduced text-only model, full tokenizer vocabulary; no trained checkpoint.
"""

import argparse
from importlib.metadata import version
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.training_masks import assistant_training_tokens
from zenithsync.training_batch import collate_training_examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if version('transformers') != '5.13.1' or version('peft') != '0.21.2':
        raise ValueError('Pinned training dependencies required')
    import torch
    from transformers import AutoTokenizer, Gemma4TextConfig, Gemma4ForCausalLM
    from peft import LoraConfig, get_peft_model

    manifest = load_json(ROOT / 'evidence/p1/model-intake-001/model-manifest.json')
    for name in ['chat_template.jinja', 'tokenizer.json', 'tokenizer_config.json']:
        record = next(row for row in manifest['files'] if row['path'] == name)
        if file_record(args.model / name) != {key: record[key] for key in ['sha256', 'size_bytes']}:
            raise ValueError('Unqualified tokenizer asset')
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    template_hash = file_record(args.model / 'chat_template.jinja')['sha256']
    histories = [[{'role': 'user', 'content': 'Say hello.'},
                  {'role': 'assistant', 'content': 'Hello 🌍'}],
                 [{'role': 'user', 'content': 'Inspect the result.'},
                  {'role': 'assistant', 'content': '', 'tool_calls': [
                      {'id': 'a', 'type': 'function', 'function': {'name': 'read_file', 'arguments': {}}}]},
                  {'role': 'tool', 'tool_call_id': 'a', 'content': 'EXTERNAL_RESULT'},
                  {'role': 'assistant', 'content': 'The result is available.'}]]
    examples = [assistant_training_tokens(tokenizer, history, template_sha256=template_hash,
                allowed_tools={'read_file'}) for history in histories]
    options = {'pad_token_id': tokenizer.pad_token_id, 'vocab_size': len(tokenizer), 'max_length': 128}
    collated = collate_training_examples(examples, **options)
    if len(set(collated['per_example_supervised_tokens'])) != 2:
        raise ValueError('Fixture must exercise unequal supervision counts')
    torch.set_num_threads(1)
    torch.manual_seed(7201)
    torch.use_deterministic_algorithms(True)
    config = Gemma4TextConfig(vocab_size=len(tokenizer), hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
        num_global_key_value_heads=1, head_dim=16, global_head_dim=16,
        hidden_size_per_layer_input=0, attention_k_eq_v=True,
        layer_types=['sliding_attention', 'full_attention'], sliding_window=8,
        max_position_embeddings=128, attention_dropout=0.0, use_cache=False)
    config._attn_implementation = 'eager'
    model = get_peft_model(Gemma4ForCausalLM(config), LoraConfig(r=2, lora_alpha=4,
        lora_dropout=0, target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj',
                                     'gate_proj', 'up_proj', 'down_proj'], bias='none'))
    model.train()
    batch = {name: torch.tensor(value) for name, value in collated['batch'].items()}
    result = model(**batch)
    batch_loss = result.loss.detach()
    result.loss.backward()
    full_gradients = {name: p.grad.detach().clone() for name, p in model.named_parameters() if p.requires_grad}
    model.zero_grad(set_to_none=True)
    weighted_loss = torch.zeros_like(batch_loss)
    for example, count in zip(examples, collated['per_example_supervised_tokens'], strict=True):
        single = collate_training_examples([example], **options)['batch']
        loss = model(**{name: torch.tensor(value) for name, value in single.items()}).loss
        weight = count / collated['supervised_tokens']
        weighted_loss += loss.detach() * weight
        (loss * weight).backward()
    torch.testing.assert_close(batch_loss, weighted_loss, rtol=1e-6, atol=1e-6)
    max_error = 0.0
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            torch.testing.assert_close(full_gradients[name], parameter.grad, rtol=1e-4, atol=1e-6)
            max_error = max(max_error, (full_gradients[name] - parameter.grad).abs().max().item())
    changed_padding = {name: value.clone() for name, value in batch.items()}
    padded = batch['attention_mask'] == 0
    if not padded.any():
        raise ValueError('Fixture must include padding')
    changed_padding['input_ids'][padded] = len(tokenizer) - 1
    with torch.no_grad():
        padding_loss = model(**changed_padding).loss
    torch.testing.assert_close(batch_loss, padding_loss, rtol=0, atol=0)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'batch.json').write_bytes(canonical_json(collated))
    (args.output / 'receipt.json').write_bytes(canonical_json({
        'schema_version': 1, 'status': 'native_batch_loss_and_gradient_checks_passed',
        'versions': {n: version(n) for n in ['torch', 'transformers', 'peft']},
        'template_sha256': template_hash, 'vocab_size': len(tokenizer),
        'per_example_supervised_tokens': collated['per_example_supervised_tokens'],
        'batch_loss': batch_loss.item(), 'weighted_microbatch_loss': weighted_loss.item(),
        'max_gradient_absolute_difference': max_error, 'padding_loss_difference': (batch_loss-padding_loss).item(),
        'sources': {name: file_record(ROOT / name) for name in ['scripts/probe_native_training_batch.py',
                    'zenithsync/training_batch.py', 'zenithsync/training_masks.py']},
        'scope': 'Native text/tool token IDs and masks with random reduced CPU Gemma; no sequence packing or full checkpoint'}))
    print('Native batching: weighted loss, accumulated gradients and padding invariance passed')


if __name__ == '__main__':
    main()
