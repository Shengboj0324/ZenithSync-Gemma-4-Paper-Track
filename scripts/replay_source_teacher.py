"""Bounded native replay of a pinned teacher trace under a reviewed profile.

Source commands are executed only inside an offline disposable source container.
Recorded observations and teacher reasoning are not used as runtime evidence.
This reviewed profile preserves action order but adapts paths and view tools;
its configured qualification ceiling does not establish model performance.
"""
import argparse
from collections import Counter
from importlib.metadata import version
import json
import os
import re
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.container_cleanup import cleanup_owned_container
from zenithsync.source_workspace import prepare_source_workspace
from zenithsync.trajectory_import import convert_swe_hero_history
from zenithsync.replay_completion import validate_completion_plan
from zenithsync.replay_correction import verify_correction_result

INSTANCE='tornadoweb__tornado-34edd2e8020b42cd16c3dc9a8c0417b9fae1e6d4'
TRACE='4d152574-6d53-4924-b9a6-c58d47a5d6d8'
PREFIX='/workspace/tornadoweb__tornado__1.0'
IMAGE='sha256:365c831bea95c20c3907b2a2f473876884dfe753a7fe6c5ac8526eaffa8701b1'


def source_path(path, prefix=PREFIX):
    if path in ('/workspace',prefix):
        return '.'
    if not isinstance(path,str) or not path.startswith(prefix+'/'):
        raise ValueError('Source path outside reviewed repository')
    relative=path[len(prefix)+1:]
    parts=relative.split('/')
    if any(p in ('','.','..','.git') for p in parts) or str(PurePosixPath(relative)) != relative:
        raise ValueError('Unsafe source path')
    return relative


NATIVE_COMMAND_SECONDS = 30


def adapt_source_search(command, prefix):
    """Map one path in a small read-only shell grammar without reserializing it.

    Quotes, BRE escapes, pipes and find's escaped terminator remain byte-exact.
    This is a replay compatibility grammar, not a general shell sandbox.
    """
    path = r'(?P<path>/[A-Za-z0-9_./-]+)'
    phrase = r'[A-Za-z_][A-Za-z_0-9]*(?: [A-Za-z_0-9]+)*'
    branch = r'[A-Za-z_][A-Za-z_0-9]*(?:\.\*[A-Za-z_0-9]+)?'
    alternatives = branch + r'(?:\\\|' + branch + r')*'
    quoted = lambda pattern: r'(?P<quote>["\'])' + pattern + r'(?P=quote)'
    glob = r'[A-Za-z0-9_.*?-]+'
    patterns = (
        r'grep -n ' + quoted(phrase) + ' ' + path,
        r'grep -n -A [1-9][0-9]? -B [1-9][0-9]? ' + quoted(alternatives) + ' ' + path,
        r'grep -rn ' + quoted(alternatives) + ' ' + path,
        r'find ' + path + r' -name ' + quoted(glob)
        + r' \| grep -i [A-Za-z_][A-Za-z_0-9]* \| head -[1-9][0-9]?',
        r'find ' + path + r' -name ' + quoted(glob)
        + r' -exec grep -l "[A-Za-z0-9_]+" \{\} \\;',
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, command)
        if match is None:
            continue
        original_path = match['path']
        # source_path also accepts /workspace for editor compatibility; these
        # shell forms require an explicit path under the original source root.
        if original_path != prefix and not original_path.startswith(prefix + '/'):
            raise ValueError('Search path outside source repository')
        relative = source_path(original_path, prefix)
        if command.startswith('grep ') and relative == '.':
            raise ValueError('Standalone grep requires a source file')
        mapped = '/workspace' + ('' if relative == '.' else '/' + relative)
        start, end = match.span('path')
        return command[:start] + mapped + command[end:]
    return None


def preflight(messages, prefix=PREFIX):
    actions=[]
    for index,message in enumerate(messages):
        for call in message.get('tool_calls',[]):
            fn=call['function'];name=fn['name'];args=fn['arguments']
            if name=='execute_bash':
                shell_metadata = {}
                if isinstance(args, dict) and set(args) == {'command', 'timeout'}:
                    if type(args['timeout']) is not int or args['timeout'] != NATIVE_COMMAND_SECONDS:
                        raise ValueError('Source timeout differs from the native command limit')
                    shell_metadata['source_timeout_seconds'] = args['timeout']
                    args = {'command': args['command']}
                if (not isinstance(args, dict) or set(args) != {'command'}
                        or not isinstance(args['command'], str)):
                    raise ValueError('Unreviewed shell invocation profile')
                if set(args)=={'command'} and isinstance(args['command'],str):
                    # This reviewed form has one literal identifier pattern and
                    # one source file. Reject shell syntax rather than reparse it
                    # into a different command or replace arbitrary substrings.
                    match=re.fullmatch(
                        r'grep -n (?P<quote>[\"\']?)(?P<pattern>[A-Za-z_][A-Za-z_0-9]*)'
                        r'(?P=quote) (?P<path>/[A-Za-z0-9_./-]+)',args['command'])
                    if match is not None:
                        relative=source_path(match['path'],prefix)
                        if relative=='.':
                            raise ValueError('Standalone grep requires a source file')
                        command=shlex.join(['grep','-n',match['pattern'],'/workspace/'+relative])
                        actions.append({'index':index,'kind':'shell','command':command, **shell_metadata})
                        continue
                search = adapt_source_search(args['command'], prefix)
                if search is not None:
                    actions.append({'index':index,'kind':'shell','command':search, **shell_metadata})
                    continue
                if set(args)=={'command'} and args['command']=='python --version':
                    actions.append({'index':index,'kind':'shell','command':args['command'], **shell_metadata})
                    continue
                if set(args)!={'command'} or not args['command'].startswith('cd '+prefix+' && '):
                    raise ValueError('Unreviewed shell invocation profile')
                command=args['command'].replace('cd '+prefix+' && ','cd /workspace && ',1)
                if prefix in command:
                    raise ValueError('Additional source-root substitution requires review')
                actions.append({'index':index,'kind':'shell','command':command, **shell_metadata})
            elif name=='str_replace_editor':
                action=args['command'];path=source_path(args['path'],prefix)
                allowed={'view':{'command','path','view_range'},
                         'create':{'command','path','file_text'},
                         'str_replace':{'command','path','old_str','new_str'}}
                if action not in allowed or set(args)-allowed[action]:
                    raise ValueError('Unsupported editor profile')
                if action!='view' and path=='.':
                    raise ValueError('Cannot edit repository directory')
                actions.append({'index':index,'kind':action,'path':path,
                                'arguments':{k:v for k,v in args.items() if k not in ('command','path')}})
            elif name in ('think','finish'):
                actions.append({'index':index,'kind':name})
            else:
                raise ValueError('Unknown source tool')
    return actions



def validate_profile(profile):
    required={'instance_id','trajectory_id','image','base_commit','source_root','repo','max_tool_calls'}
    if not isinstance(profile,dict) or set(profile)!=required:
        raise ValueError('Exact replay profile fields required')
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',profile['repo']) is None:
        raise ValueError('Invalid repository')
    if re.fullmatch(re.escape(profile['repo'].replace('/','__'))+r'-(?:[0-9a-f]{40}|[1-9][0-9]*)',profile['instance_id']) is None:
        raise ValueError('Instance/repository mismatch')
    if re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',profile['trajectory_id']) is None:
        raise ValueError('Invalid trajectory ID')
    if re.fullmatch(r'sha256:[0-9a-f]{64}',profile['image']) is None:
        raise ValueError('Immutable local image required')
    if re.fullmatch(r'[0-9a-f]{40}',profile['base_commit']) is None:
        raise ValueError('Full base commit required')
    if re.fullmatch(r'/workspace/[A-Za-z0-9_-][A-Za-z0-9_.-]*',profile['source_root']) is None:
        raise ValueError('Simple source-root directory required')
    if type(profile['max_tool_calls']) is not int or not 1<=profile['max_tool_calls']<=100:
        raise ValueError('Replay call ceiling must be 1-100')
    return profile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',type=Path)
    p.add_argument('--completion-plan',type=Path,
                   help='Explicit hash-bound assistant actions before source terminal submission')
    p.add_argument('--source-shard',type=Path,default=ROOT/'artifacts/data/quarantine/swe-hero-001/data/train-00000-of-00014.parquet')
    p.add_argument('--source-intake',type=Path,default=ROOT/'evidence/data/swe-hero-intake-001/receipt.json')
    runtime=p.add_mutually_exclusive_group()
    runtime.add_argument('--biolink-offline',action='store_true',help='Use inspected task-172 runtime and public schema replay')
    runtime.add_argument('--conda-testbed',action='store_true',help='Use reviewed /opt/conda/envs/testbed runtime with no installer leftover')
    runtime.add_argument('--miniconda-testbed',action='store_true',help='Use reviewed /opt/miniconda3/envs/testbed runtime with no installer leftover')
    args=p.parse_args()
    profile=validate_profile(json.loads(args.profile.read_text()) if args.profile else {
        'instance_id':INSTANCE,'trajectory_id':TRACE,'image':IMAGE,
        'base_commit':'8a9179f2d35e353782aa3611dbdd79c29a5e8185',
        'source_root':PREFIX,'repo':'tornadoweb/tornado','max_tool_calls':100})
    instance=profile['instance_id'];trace=profile['trajectory_id'];image=profile['image']
    for name,pinned in {'swegemma':'0.2.10','adk-submission':'0.2.13',
                        'google-adk':'1.36.1','adk-eval-core':'0.1.0'}.items():
        if version(name)!=pinned: raise ValueError('Pinned native runtime required')
    import pyarrow.parquet as pq
    shard=args.source_shard
    intake=json.loads(args.source_intake.read_text())
    identity=file_record(shard)
    if (intake['dataset']!='nvidia/SWE-Hero-openhands-trajectories'
            or intake['revision']!='150bc119e52c647216fce285fd801f16b6fd745b'
            or identity not in intake['downloaded'].values()):
        raise ValueError('Teacher provenance mismatch')
    official=json.loads((ROOT/'evidence/p1/task-index-001/receipt.json').read_text())
    if profile['repo'].casefold() in {r.casefold() for r in official['repo_counts']}:
        raise ValueError('Reserved repository excluded before source body read')
    matches=pq.read_table(shard,columns=['instance_id','trajectory_id','trajectory'],
                         filters=[('trajectory_id','=',trace)]).to_pylist()
    if len(matches)!=1 or matches[0]['instance_id']!=instance or file_record(shard)!=identity:
        raise ValueError('Teacher task linkage mismatch')
    converted=convert_swe_hero_history(matches[0]['trajectory'])
    actions=preflight(converted['messages'],profile['source_root'])
    completion = None
    completion_identity = None
    if args.completion_plan is not None:
        completion = validate_completion_plan(json.loads(args.completion_plan.read_text()))
        completion_identity = file_record(args.completion_plan)
        if (not actions or actions[-1]['kind'] != 'finish'
                or sum(a['kind'] == 'finish' for a in actions) != 1):
            raise ValueError('Completion requires one final source terminal')
        if sum(a['kind'] not in ('think', 'finish') for a in actions) + len(completion['commands']) > profile['max_tool_calls']:
            raise ValueError('Completion exceeds explicit native tool budget')
    from swegemma.context import SwegemmaContext
    from swegemma.sandbox import ContainerConfig,ContainerManager
    os.environ.setdefault('DOCKER_HOST',subprocess.check_output(
        ['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'],text=True,timeout=15).strip())
    environment={'TEST_TMPDIR':'/tmp'}
    if args.biolink_offline or args.conda_testbed or args.miniconda_testbed:
        runtime_bin='/opt/miniconda3/envs/testbed/bin' if args.miniconda_testbed else '/opt/conda/envs/testbed/bin'
        environment.update(PATH=runtime_bin+':/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                           PYTHONDONTWRITEBYTECODE='1')
    if args.biolink_offline:
        if instance!='biolink__biolink-model-toolkit-172':
            raise ValueError('Biolink resource profile only qualified for task 172')
        environment.update(PYTHONPATH='/opt/zenithsync-resource-replay')
    manager=ContainerManager(ContainerConfig(image=image,reuse_containers=False,environment=environment))
    manager.client.images.get(image)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'actions.json').write_bytes(canonical_json(actions))
    if completion is not None and file_record(args.output/'actions.json') != completion['source_actions']:
        raise ValueError('Completion plan source action identity mismatch')
    receipt={'source':identity,'trajectory_id':trace,'instance_id':instance,
        'profile':profile,'image':image,'script':file_record(Path(__file__)),
        'action_counts':dict(Counter(a['kind'] for a in actions)),
        'training_approved':False,'new_model_evaluated':False,
        'source_observations_reused':False,'status':'incomplete',
        'environment':environment,
        'limits':{'tool_calls':profile['max_tool_calls'],'minutes':10,'command_seconds':NATIVE_COMMAND_SECONDS}}
    if completion is not None:
        receipt.update(completion_plan=completion, completion_plan_file=completion_identity,
                       completion_module=file_record(ROOT/'zenithsync/replay_completion.py'))
    cid=None;events=[]
    try:
        cid=manager.start()
        attrs=manager.client.containers.get(cid).attrs
        if attrs['HostConfig']['NetworkMode']!='none' or attrs['Mounts']:
            raise ValueError('Offline unmounted source container required')
        provenance=json.loads(manager.exec(cid,'cat /opt/zenithsync/source-snapshot.json',timeout=30).stdout)
        if provenance['base_commit']!=profile['base_commit']:
            raise ValueError('Wrong source base')
        prepare_source_workspace(manager,cid,snapshot_commit=provenance['snapshot_commit'],
                                 source_tree=provenance['source_tree'],installer_leftover=not (args.biolink_offline or args.conda_testbed or args.miniconda_testbed))
        if args.biolink_offline:
            from zenithsync.replay_resources import stage_resources
            receipt['offline_resources']=stage_resources(manager,cid,
                ROOT/'evidence/data/swe-rebench-biolink-resources-001',ROOT/'zenithsync/offline_resources.py')
            check=manager.exec(cid,"python -c 'from bmt import Toolkit; assert Toolkit().get_model_version()==\"4.2.1\"'",timeout=30)
            if check.exit_code:
                raise ValueError('Offline resource startup check failed: '+check.stderr)
        ctx=SwegemmaContext(docker_manager=manager,container_id=cid,task_id=trace,
            repo=profile['repo'],max_tool_calls=profile['max_tool_calls'],max_time_minutes=10,max_exec_seconds=NATIVE_COMMAND_SECONDS,
            graph_dir='/nonexistent-fixture',embeddings_dir='/nonexistent-fixture')
        ctx.start_agent_session()
        raw_tools=ctx.create_tools()
        native_calls=[]
        def capture(name,function):
            def invoke(**kwargs):
                result=function(**kwargs)
                native_calls.append({'name':name,'arguments':kwargs,'result':result})
                return result
            return invoke
        tools={name:capture(name,function) for name,function in raw_tools.items()}
        receipt['available_tools']=sorted(tools)
        for action in actions:
            kind=action['kind'];a=action.get('arguments',{});path=action.get('path')
            native_start=len(native_calls)
            if kind=='think':
                result={'status':'not_executed','reason':'teacher reasoning is not a native tool'}
            elif kind=='finish':
                if completion is not None:
                    for command in completion['commands']:
                        completion_start=len(native_calls)
                        observed=tools['run_command'](command=command['command'])
                        events.append({'source_index':None,'adapter_authored':True,
                            'kind':'completion','result':observed,
                            'native_calls':native_calls[completion_start:]})
                        (args.output/'events.json').write_bytes(canonical_json(events))
                        verify_correction_result(observed,command['expected_exit_code'])
                    native_start=len(native_calls)
                result=tools['submit_patch']()
            elif kind=='shell':
                result=tools['run_command'](command=action['command'])
            elif kind=='view':
                directory=manager.exec(cid,'test -d '+shlex.quote('/workspace/'+path),timeout=10)
                if directory.exit_code==0:
                    if 'view_range' in a: raise ValueError('Directory view with line range')
                    result=tools['run_command'](command='find '+shlex.quote(path)+' -maxdepth 2 -not -path "*/.git/*" -not -path "*/.venv/*" | head -200')
                else:
                    bounds=a.get('view_range')
                    kwargs={}
                    if bounds:
                        kwargs={'start_line':bounds[0],'end_line':None if bounds[1]==-1 else bounds[1]}
                    result=tools['read_file'](filepath=path,**kwargs)
            elif kind=='create':
                exists=manager.exec(cid,'test -e '+shlex.quote('/workspace/'+path),timeout=10)
                if exists.exit_code==0: raise ValueError('Source create would overwrite existing path')
                result=tools['write_file'](filepath=path,content=a['file_text'])
            elif kind=='str_replace':
                result=tools['edit_file'](filepath=path,old_string=a['old_str'],new_string=a['new_str'])
            events.append({'source_index':action['index'],'kind':kind,'result':result,
                           'native_calls':native_calls[native_start:]})
            (args.output/'events.json').write_bytes(canonical_json(events))
            if kind in ('create','str_replace','finish') and result['status']!='ok':
                raise RuntimeError('Mutation or submission failed; replay stopped')
            print({'source_index':action['index'],'kind':kind,'status':result['status']},flush=True)
        if not ctx.submitted_patch: raise ValueError('No submitted patch')
        (args.output/'submitted.patch').write_text(ctx.submitted_patch)
        if completion is not None:
            if file_record(args.completion_plan) != completion_identity:
                raise ValueError('Completion plan changed during replay')
            if file_record(args.output/'submitted.patch') != completion['final_patch']:
                raise ValueError('Native submitted patch differs from completion plan')
        receipt.update(status='replayed_not_graded',patch=file_record(args.output/'submitted.patch'),
                       tool_calls=ctx.tool_calls)
    finally:
        if cid is not None:receipt['cleanup']=cleanup_owned_container(manager,cid)
        (args.output/'receipt.json').write_bytes(canonical_json(receipt))
    if receipt['cleanup']['removed'] is not True:raise RuntimeError('Cleanup unverified')


if __name__=='__main__':main()
