"""Exercise the installed official tool-to-model Unicode serialization path.

Synthetic adapter fixtures only; no model, sandbox file read, or repair claim.
"""

import argparse
import asyncio
import hashlib
from importlib.metadata import version
import inspect
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
from zenithsync.artifacts import canonical_json, file_record


async def run(output):
    if version('google-adk') != '1.36.1' or version('swegemma') != '0.2.10':
        raise ValueError('Qualified adapter versions required')
    from google.adk.models import lite_llm
    from google.genai import types
    from swegemma.tools import base
    sources = {}
    for module, wheel, member in [
        (lite_llm, 'google_adk-1.36.1-py3-none-any.whl', 'google/adk/models/lite_llm.py'),
        (base, 'swegemma-0.2.10-py3-none-any.whl', 'swegemma/tools/base.py'),
    ]:
        path = Path(inspect.getfile(module))
        with zipfile.ZipFile(ROOT/'artifacts/official/wheelhouse'/wheel) as archive:
            original = archive.read(member)
        if path.read_bytes() != original:
            raise ValueError('Installed adapter differs from released wheel')
        sources[member] = {'sha256': hashlib.sha256(original).hexdigest(), 'wheel': wheel}
    fixtures = {
        'non_bmp': 'hello 🌍',
        'multilingual': '中文 日本語 العربية',
        'combining': 'é e\u0301',
        'literal_backslashes': r'\ud83c\udf0d \n C:\new\test',
        'code': 'data = {"text": "🌍"}\nprint(data["text"])\n',
        'controls': 'first\tsecond\r\nlast\x00',
    }
    results = []
    for name, text in fixtures.items():
        payload = base.parse_tool_response(base.ok_response(content=text))
        content = types.Content(role='user', parts=[types.Part(function_response=types.FunctionResponse(
            id='probe_'+name, name='read_file', response=payload))])
        message = await lite_llm._content_to_message_param(
            content, provider='openai', model='openai/gemma-4-31b-it-qat-w4a16-ct')
        if message['role'] != 'tool' or message['tool_call_id'] != 'probe_'+name:
            raise ValueError('Tool linkage changed')
        serialized = message['content']
        recovered = json.loads(serialized)
        if recovered != payload or recovered['content'].encode('utf-8') != text.encode('utf-8'):
            raise ValueError('Tool response content changed')
        if any(ord(c)>127 and c not in serialized for c in text):
            raise ValueError('Non-ASCII scalar was escaped in model-facing content')
        results.append({'fixture': name, 'status': 'passed',
                        'original_utf8_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                        'model_facing_content': serialized})
    output.mkdir(parents=True, exist_ok=False)
    (output/'receipt.json').write_bytes(canonical_json({
        'status': 'official_text_adapter_unicode_checks_passed', 'checks': results,
        'sources': sources, 'verifier': file_record(Path(__file__)),
        'scope': 'Actual released Python adapters with synthetic responses; no file tool or model execution'}))
    print('Official tool-to-model Unicode boundary:', len(results), 'fixtures passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    asyncio.run(run(parser.parse_args().output))
