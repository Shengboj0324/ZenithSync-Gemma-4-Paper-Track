"""Exercise the shared qualification engine on a reduced compressed Gemma."""

import argparse
from importlib.metadata import version
from pathlib import Path
import sys
import weakref

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record
from zenithsync.training_batch import collate_training_examples
from zenithsync.training_pilot import qualify_adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    required = {'transformers': '5.13.1', 'compressed-tensors': '0.15.0.1', 'peft': '0.21.2'}
    if any(version(name) != value for name, value in required.items()):
        raise ValueError('Pinned loader dependencies required')
    import torch
    from transformers import Gemma4ForCausalLM, CompressedTensorsConfig

    torch.set_num_threads(1)
    torch.manual_seed(7401)
    torch.use_deterministic_algorithms(True)
    references = []

    def load_base():
        if any(reference() is not None for reference in references):
            raise ValueError('Previous base model remains alive during reload')
        model = Gemma4ForCausalLM.from_pretrained(args.checkpoint, local_files_only=True,
            quantization_config=CompressedTensorsConfig(run_compressed=False),
            dtype=torch.bfloat16, attn_implementation='eager')
        references.append(weakref.ref(model))
        return model

    # Derive shapes independently from this fixture's documented architecture.
    shapes = {}
    for layer in range(2):
        prefix = f'model.layers.{layer}'
        for projection, shape in {'q_proj': [64, 64], 'k_proj': [32, 64],
                                  'o_proj': [64, 64]}.items():
            shapes[f'{prefix}.self_attn.{projection}'] = shape
        if layer == 0:
            shapes[f'{prefix}.self_attn.v_proj'] = [32, 64]
        for projection, shape in {'gate_proj': [128, 64], 'up_proj': [128, 64],
                                  'down_proj': [64, 128]}.items():
            shapes[f'{prefix}.mlp.{projection}'] = shape
    row = collate_training_examples(
        [{'input_ids': [2, 3, 4, 5, 1], 'labels': [-100, -100, 4, 5, 1]}],
        pad_token_id=0, vocab_size=64, max_length=64)
    batch = {key: torch.tensor(value) for key, value in row['batch'].items()}
    result = qualify_adapter(load_base=load_base, batch=batch, target_shapes=shapes,
                             output=args.output, learning_rate=0.005)
    (args.output / 'probe.json').write_bytes(canonical_json({
        'versions': {name: version(name) for name in [*required, 'torch']},
        'scope': 'Reduced random BF16 CPU Gemma; synthetic IDs; no native tokenizer or CUDA',
        'independent_base_loads': len(references),
        'prior_base_released_before_reload': True,
        'sources': {str(path.relative_to(ROOT)): file_record(path) for path in [
            Path(__file__), ROOT / 'zenithsync/training_pilot.py',
            ROOT / 'zenithsync/training_state.py']}}))
    print({key: result[key] for key in ['status', 'loss', 'trainable_parameters',
                                      'adapter_effect_max_abs', 'reload_max_abs_error']})


if __name__ == '__main__':
    main()
