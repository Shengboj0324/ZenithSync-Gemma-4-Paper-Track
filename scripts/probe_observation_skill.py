"""Compile the candidate and exercise ADK's real materialized skill wrapper locally."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = {'google-adk': '1.36.1', 'adk-submission': '0.2.13', 'swegemma': '0.2.10'}
    if any(version(name) != wanted for name, wanted in expected.items()):
        raise ValueError('Pinned compiler and ADK required')
    from adk_submission import ModelRegistry, ToolRegistry, compile_submission
    from google.adk.code_executors.base_code_executor import BaseCodeExecutor
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools.skill_toolset import _SkillScriptCodeExecutor, SkillToolset
    from swegemma.config import build_submission_limits
    from adk_submission.yaml_loader import load_yaml
    candidate = ROOT/'candidates/p1-observation-memory'
    config = load_yaml(candidate/'agent.yaml', candidate)
    tools = ToolRegistry()
    def unavailable():
        raise AssertionError('Registry fixtures must never execute')
    for name in config['tools']:
        tools.register(name, unavailable)
    models = ModelRegistry()
    models.register(config['model'], config['model'])
    class UnusedExecutor(BaseCodeExecutor):
        def execute_code(self, invocation_context, code_execution_input):
            raise AssertionError('Compiler must not execute skill scripts')
    limits, generation = build_submission_limits()
    agent = compile_submission(candidate, tool_registry=tools, model_registry=models,
        code_executor=UnusedExecutor(), limits=limits, generation_constraints=generation)
    if sum(isinstance(tool, SkillToolset) for tool in agent.tools) != 1:
        raise AssertionError('Expected compiled skill toolset')
    skill = load_skill_from_dir(candidate/'skills/source-observations')
    helper = _SkillScriptCodeExecutor(UnusedExecutor(), 10)
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp).resolve()
        repo = store/'repository'
        repo.mkdir()
        source = repo/'module.py'
        source.write_text('value = "α"\nreturn_value = value\n')
        before = file_record(source)
        def invoke(arguments):
            wrapper = helper._build_wrapper_code(skill, 'scripts/observe.py',
                ['--workspace', str(repo), *arguments])
            result = subprocess.run([sys.executable, '-I', '-B', '-c', wrapper],
                cwd=store, env={**os.environ, 'TMPDIR': str(store)}, text=True,
                capture_output=True, timeout=15, check=True)
            return json.loads(result.stdout)
        captured = invoke(['snapshot', '--path', 'module.py', '--start', '1', '--end', '1'])
        handle = captured['handle']
        recalled = invoke(['recall', '--handle', handle])
        if recalled['status'] != 'current_source_match' or recalled['record']['excerpt'] != 'value = "α"\n':
            raise AssertionError('Wrapper recall did not preserve exact Unicode source')
        if file_record(source) != before or list(repo.iterdir()) != [source]:
            raise AssertionError('Snapshot modified source or repository inventory')
        source.write_text('value = "α"\nreturn_value = None\n')
        stale = invoke(['recall', '--handle', handle])
        if stale['status'] != 'stale' or 'record' in stale:
            raise AssertionError('Changed source did not invalidate the observation')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'candidate-manifest.json').write_bytes(canonical_json(inventory(candidate,
        kind='candidate', source='Experimental source-observation recovery candidate', revision='untrained-001')))
    (args.output/'receipt.json').write_bytes(canonical_json({'schema_version': 1,
        'status': 'compiler_and_materialized_wrapper_passed', 'versions': expected,
        'checks': ['skill toolset compiled', 'exact Unicode recall across separate processes',
                   'source unchanged and no repository artifacts', 'stale outside-excerpt edit detected'],
        'probe': file_record(Path(__file__)), 'candidate_manifest': file_record(args.output/'candidate-manifest.json'),
        'scope': 'Compiler registry fixtures and actual ADK wrapper run in local isolated Python processes. '
                 'No production sandbox executor, model skill selection, compaction recovery behavior, '
                 'patch extraction or repair-quality comparison qualified.'}))
    print('Candidate compilation and actual wrapper snapshot/recall/staleness passed')


if __name__ == '__main__':
    main()
