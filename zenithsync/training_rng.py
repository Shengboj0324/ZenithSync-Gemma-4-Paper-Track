"""Process RNG checkpoints for quiescent CPU or CUDA training.

Includes Python, NumPy's legacy global generator, and Torch global generators.
Custom Generator objects and data-loader workers require their own checkpoints.
Restoration must occur after model/optimizer construction and before training.
"""
import random
import sys


def _runtime():
    import torch
    cuda = torch.cuda.is_initialized()
    return {
        'python_version': list(sys.version_info[:3]),
        'torch_version': str(torch.__version__),
        'cuda_initialized': cuda,
        'cuda_devices': [torch.cuda.get_device_name(i)
                         for i in range(torch.cuda.device_count())] if cuda else [],
        'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
        'deterministic_warn_only': torch.is_deterministic_algorithms_warn_only_enabled(),
        'cudnn_benchmark': torch.backends.cudnn.benchmark,
        'cudnn_deterministic': torch.backends.cudnn.deterministic,
        'float32_matmul_precision': torch.get_float32_matmul_precision(),
    }


def capture_rng_state():
    import numpy as np
    import torch
    numpy_state = np.random.get_state()
    runtime = _runtime()
    return {
        'schema_version': 1,
        'runtime': runtime,
        'numpy_version': str(np.__version__),
        'python': random.getstate(),
        'numpy': (numpy_state[0], numpy_state[1].tolist(),
                  int(numpy_state[2]), int(numpy_state[3]), float(numpy_state[4])),
        'torch_cpu': torch.get_rng_state().clone(),
        'torch_cuda': [state.clone() for state in torch.cuda.get_rng_state_all()]
                      if runtime['cuda_initialized'] else [],
    }


def validate_rng_state(payload):
    """Validate using private generators before mutating global RNG state.

    Runtime equality is necessary, not sufficient, for deterministic execution.
    Unsupported generators (including MPS) must not be used by this training path.
    """
    import math
    import numpy as np
    import torch

    fields = {'schema_version', 'runtime', 'numpy_version', 'python', 'numpy',
              'torch_cpu', 'torch_cuda'}
    if (not isinstance(payload, dict) or set(payload) != fields
            or type(payload['schema_version']) is not int or payload['schema_version'] != 1):
        raise ValueError('Invalid RNG checkpoint schema')
    if payload['runtime'] != _runtime() or payload['numpy_version'] != str(np.__version__):
        raise ValueError('RNG runtime or determinism settings changed')
    python_probe = random.Random()
    python_probe.setstate(payload['python'])
    state = payload['numpy']
    if (not isinstance(state, tuple) or len(state) != 5 or state[0] != 'MT19937'
            or not isinstance(state[1], list) or len(state[1]) != 624
            or any(type(value) is not int or not 0 <= value < 2**32 for value in state[1])
            or type(state[2]) is not int or not 0 <= state[2] <= 624
            or type(state[3]) is not int or state[3] not in (0, 1)
            or type(state[4]) is not float or not math.isfinite(state[4])):
        raise ValueError('Invalid NumPy global RNG state')
    numpy_state = (state[0], np.array(state[1], dtype=np.uint32), *state[2:])
    np.random.RandomState().set_state(numpy_state)
    cuda_states = payload['torch_cuda']
    if not isinstance(cuda_states, list) or len(cuda_states) != len(payload['runtime']['cuda_devices']):
        raise ValueError('CUDA generator topology changed')
    devices = ['cpu'] + ['cuda:' + str(i) for i in range(len(cuda_states))]
    states = [payload['torch_cpu'], *cuda_states]
    for device, value in zip(devices, states, strict=True):
        if (not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                or value.dtype != torch.uint8 or value.ndim != 1 or not value.is_contiguous()):
            raise ValueError('Invalid Torch RNG tensor')
        torch.Generator(device=device).set_state(value)
    return numpy_state


def restore_rng_state(payload):
    import numpy as np
    import torch
    numpy_state = validate_rng_state(payload)
    # Validation does not draw from or reset any global training generator.
    random.setstate(payload['python'])
    np.random.set_state(numpy_state)
    torch.set_rng_state(payload['torch_cpu'])
    if payload['torch_cuda']:
        torch.cuda.set_rng_state_all(payload['torch_cuda'])
