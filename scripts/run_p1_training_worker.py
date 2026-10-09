"""Full-checkpoint one-update worker. Invoke through a deadline supervisor.

No implicit downloads, CPU offload, corpus training or Pod lifecycle changes.
"""

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.quantized_layout import expected_projections
from zenithsync.training_fixture import prepare_pilot_batch
from zenithsync.training_pilot import qualify_adapter
from zenithsync.gpu_memory import DeviceMemoryMonitor


def require_volume(path, volume_root):
    root = volume_root.resolve(strict=True)
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('Path escapes required persistent volume: ' + str(path))
    probe = resolved
    while not probe.exists():
        probe = probe.parent
    result = subprocess.run(['findmnt', '--json', '--target', str(probe),
                             '--output', 'TARGET,FSTYPE,SOURCE'], check=True,
                            capture_output=True, text=True, timeout=10)
    mounts = json.loads(result.stdout)['filesystems']
    if len(mounts) != 1 or mounts[0]['target'] != str(root):
        raise ValueError('Path does not use the required mounted filesystem')
    if mounts[0]['fstype'] in ['overlay', 'tmpfs', 'ramfs']:
        raise ValueError('Ephemeral filesystem rejected')
    return mounts[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--volume-root', type=Path, default=Path('/workspace'))
    args = parser.parse_args()
    if platform.system() != 'Linux' or sys.version_info[:2] != (3, 12):
        raise ValueError('Qualified Linux Python 3.12 runtime required')
    if file_record(args.manifest)['sha256'] != args.manifest_sha256:
        raise ValueError('Manifest differs from independently supplied identity')
    mounts = {name: require_volume(path, args.volume_root)
              for name, path in [('model', args.model), ('output', args.output)]}
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        required = {'torch': '2.10.0', 'transformers': '5.13.1',
                    'compressed-tensors': '0.15.0.1', 'peft': '0.21.2'}
        versions = {name: version(name) for name in required}
        if any(versions[name].split('+')[0] != value for name, value in required.items()):
            raise ValueError('Training runtime versions differ from qualified pins')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['OMP_NUM_THREADS'] = '4'
        os.environ['MKL_NUM_THREADS'] = '4'
        import torch
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        from transformers import Gemma4ForConditionalGeneration, CompressedTensorsConfig
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise ValueError('Exactly one visible CUDA GPU required')
        # Reject other visible compute clients; free-memory admission alone does
        # not establish absence of a competing server.
        clients = subprocess.run(['nvidia-smi', '--query-compute-apps=pid',
                                  '--format=csv,noheader,nounits'], check=True,
                                 capture_output=True, text=True, timeout=10)
        if any(line.strip() != str(os.getpid()) for line in clients.stdout.splitlines() if line.strip()):
            raise ValueError('Another GPU compute process is active')
        free, total = torch.cuda.mem_get_info()
        if free < 70 * 1024**3:
            raise ValueError('Less than 70 GiB free device memory; admission denied')
        torch.manual_seed(7401)
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        manifest = load_json(args.manifest)
        verify(args.model, manifest)
        config = load_json(args.model / 'config.json')
        shapes = expected_projections(config)
        if len(shapes) != 410 or 4 * sum(rows + cols for rows, cols in shapes.values()) != 30607360:
            raise ValueError('Checkpoint does not match qualified full-model projection coverage')
        fixture = prepare_pilot_batch(args.model, manifest)
        (args.output / 'fixture.json').write_bytes(canonical_json(fixture))
        batch = {key: torch.tensor(value, device='cuda:0') for key, value in fixture['batch'].items()}
        torch.cuda.reset_peak_memory_stats()
        loads = []

        def load_base():
            model = Gemma4ForConditionalGeneration.from_pretrained(args.model,
                local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16,
                quantization_config=CompressedTensorsConfig(run_compressed=False),
                attn_implementation='eager', device_map={'': 'cuda:0'})
            if any(value.device.type != 'cuda' for value in model.parameters()):
                raise ValueError('CPU/meta/offloaded model parameter rejected')
            if any('weight_packed' in name for name, _ in model.named_parameters()):
                raise ValueError('Packed parameters remain after decompression')
            loads.append({'allocated_bytes': torch.cuda.memory_allocated(),
                          'reserved_bytes': torch.cuda.memory_reserved()})
            return model

        with DeviceMemoryMonitor(args.output / 'device-memory.jsonl') as monitor:
            qualify_adapter(load_base=load_base, batch=batch, target_shapes=shapes,
                            output=args.output / 'qualification')
            torch.cuda.synchronize()
        (args.output / 'worker.json').write_bytes(canonical_json({
            'schema_version': 1, 'status': 'full_checkpoint_one_update_reload_passed',
            'versions': versions, 'mounts': mounts, 'model_manifest': file_record(args.manifest),
            'cpu_threads': {'intraop': torch.get_num_threads(), 'interop': torch.get_num_interop_threads()},
            'initial_free_bytes': free, 'device_total_bytes': total, 'load_samples': loads,
            'peak_torch_allocated_bytes': torch.cuda.max_memory_allocated(),
            'peak_torch_reserved_bytes': torch.cuda.max_memory_reserved(),
            'device_memory': monitor.summary(),
            'scope': 'One synthetic native-tokenized update; no training corpus or performance qualification',
            'memory_scope': 'Allocator peaks plus separate sampled device-wide measurements'}))
    except BaseException:
        (args.output / 'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
