"""Full Gemma corpus worker. Run through run_corpus_training.py's supervisor.

No downloads, CPU offload, Pod lifecycle changes or quarantine admission bypass.
"""
import argparse
import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_p1_training_worker import require_volume
from zenithsync.artifacts import canonical_json, file_record, load_json, verify
from zenithsync.corpus_run import preflight_corpus_run
from zenithsync.quantized_layout import expected_projections


WORKER_SOURCES = [
        'scripts/run_corpus_training_worker.py','zenithsync/gemma_training.py',
        'zenithsync/training_session.py','zenithsync/corpus_training.py',
        'zenithsync/corpus_optimization.py','zenithsync/training_rng.py',
        'zenithsync/adapter_checkpoint.py','zenithsync/optimizer_checkpoint.py',
        'zenithsync/checkpoint_storage.py','zenithsync/training_batch.py',
        'zenithsync/training_corpus.py','zenithsync/training_schedule.py',
        'zenithsync/training_state.py','zenithsync/corpus_run.py',
        'zenithsync/artifacts.py','zenithsync/contracts.py','zenithsync/splits.py',
        'zenithsync/quantized_layout.py','zenithsync/gpu_memory.py',
        'scripts/run_p1_training_worker.py']

def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'manifest', 'corpus', 'schedule', 'config', 'output'):
        result.add_argument('--'+name, type=Path, required=True)
    for name in ('manifest', 'corpus', 'schedule', 'config'):
        result.add_argument('--'+name+'-sha256', required=True)
    result.add_argument('--volume-root', type=Path, default=Path('/workspace'))
    result.add_argument('--resume', type=Path)
    result.add_argument('--resume-sha256')
    result.add_argument('--resume-size', type=int)
    return result


def main():
    args = parser().parse_args()
    corpus, schedule, config = preflight_corpus_run(
        corpus_root=args.corpus, corpus_sha256=args.corpus_sha256,
        schedule_path=args.schedule, schedule_sha256=args.schedule_sha256,
        config_path=args.config, config_sha256=args.config_sha256)
    resume_fields = [args.resume is not None, args.resume_sha256 is not None, args.resume_size is not None]
    if any(resume_fields) and not all(resume_fields):
        raise ValueError('Resume requires path, SHA-256 and size together')
    if args.resume is not None and file_record(args.resume) != {
            'sha256':args.resume_sha256,'size_bytes':args.resume_size}:
        raise ValueError('Resume checkpoint file identity mismatch')
    if platform.system() != 'Linux' or sys.version_info[:2] != (3, 12):
        raise ValueError('Pinned Linux Python 3.12 runtime required')
    locations = {name: getattr(args, name) for name in ('model','manifest','corpus','schedule','config','output')}
    if args.resume is not None:locations['resume'] = args.resume
    mounts = {name: require_volume(path, args.volume_root) for name, path in locations.items()}
    if file_record(args.manifest)['sha256'] != args.manifest_sha256:
        raise ValueError('Model manifest identity differs')
    manifest = load_json(args.manifest)
    verify(args.model, manifest)
    assets = load_json(args.corpus/'corpus.json')['tokenizer_assets']
    model_files = {row['path']: {key: row[key] for key in ('sha256','size_bytes')}
                   for row in manifest['files']}
    if any(model_files.get(name) != identity for name, identity in assets.items()):
        raise ValueError('Corpus tokenizer assets differ from the verified model')
    shapes = expected_projections(load_json(args.model/'config.json'))
    if len(shapes) != 410 or 4*sum(a+b for a,b in shapes.values()) != 30607360:
        raise ValueError('Model differs from qualified 31B projection layout')
    required = {'torch':'2.10.0', 'transformers':'5.13.1',
                'compressed-tensors':'0.15.0.1', 'peft':'0.21.2'}
    versions = {name: version(name) for name in required}
    if any(versions[name].split('+')[0] != pin for name,pin in required.items()):
        raise ValueError('Training runtime differs from qualified pins')
    sources = {name:file_record(ROOT/name) for name in WORKER_SOURCES}
    execution_config = {'config_sha256':args.config_sha256,'sources':sources,'versions':versions,
                        'adapter':{'rank':4,'alpha':8,'dropout':0.0},
                        'dtype':'bfloat16','attention':'eager'}
    execution_sha256 = hashlib.sha256(canonical_json(execution_config)).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                          CUBLAS_WORKSPACE_CONFIG=':4096:8', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4')
        import numpy as np
        import torch
        from transformers import Gemma4ForConditionalGeneration, CompressedTensorsConfig
        from zenithsync.gemma_training import attach_training_adapter
        from zenithsync.adapter_checkpoint import frozen_state
        from zenithsync.training_session import run_training_session
        from zenithsync.gpu_memory import DeviceMemoryMonitor
        torch.set_num_threads(4);torch.set_num_interop_threads(1)
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise ValueError('Exactly one visible CUDA device required')
        clients = subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],
                                 check=True,capture_output=True,text=True,timeout=10)
        if any(line.strip() != str(os.getpid()) for line in clients.stdout.splitlines() if line.strip()):
            raise ValueError('Another GPU compute process is active')
        free, total = torch.cuda.mem_get_info()
        if free < 70*1024**3:raise ValueError('At least 70 GiB free device memory required')
        random.seed(config['seed']);np.random.seed(config['seed'] % 2**32);torch.manual_seed(config['seed'])
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        bindings = {'base_manifest_sha256':args.manifest_sha256,
                    'corpus_manifest_sha256':args.corpus_sha256,
                    'corpus_content_sha256':corpus.summary['content_sha256'],
                    'schedule_sha256':schedule['schedule_sha256'],
                    'worker_config_sha256':execution_sha256}
        resume = None if args.resume is None else {'path':str(args.resume),
            'identity':{'sha256':args.resume_sha256,'size_bytes':args.resume_size}}
        torch.cuda.reset_peak_memory_stats()
        with DeviceMemoryMonitor(args.output/'device-memory.jsonl') as monitor:
            base = Gemma4ForConditionalGeneration.from_pretrained(args.model,
                local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16,
                quantization_config=CompressedTensorsConfig(run_compressed=False),
                attn_implementation='eager', device_map={'':'cuda:0'})
            if any(p.device.type != 'cuda' or 'weight_packed' in name for name,p in base.named_parameters()):
                raise ValueError('Offloaded or packed base parameters rejected')
            model = attach_training_adapter(base, shapes)
            frozen = frozen_state(model)
            optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                lr=config['learning_rate'],weight_decay=0,foreach=False,fused=False)
            session = run_training_session(model,optimizer,corpus=corpus,schedule=schedule,
                bindings=bindings,expected_frozen=frozen,output=args.output/'checkpoints',resume=resume,
                **{key:config[key] for key in ('max_updates','max_seconds','max_sequence_tokens',
                                               'max_checkpoint_bytes','max_session_checkpoint_bytes')})
            torch.cuda.synchronize()
        if any(file_record(ROOT/name) != identity for name,identity in sources.items()):
            raise ValueError('Worker implementation changed during training')
        (args.output/'worker.json').write_bytes(canonical_json({
            'schema_version':1,'status':'corpus_session_returned','session':session,
            'versions':versions,'mounts':mounts,'bindings':bindings,
            'execution_config':execution_config,
            'initial_free_bytes':free,'device_total_bytes':total,
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
            'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'device_memory':monitor.summary(),
            'scope':'Training session evidence; no held-out repair quality claim'}))
    except BaseException:
        (args.output/'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':main()
