import unittest
from scripts.replay_tornado_teacher import PREFIX,preflight,source_path


def call(name,arguments):
    return [{'tool_calls':[{'function':{'name':name,'arguments':arguments}}]}]


class TeacherReplayProfileTests(unittest.TestCase):
    def test_source_runtime_options_are_mutually_exclusive(self):
        import subprocess
        import sys
        from pathlib import Path
        result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/replay_source_teacher.py'),
            '--output','/tmp/zenithsync-unused-argument-check','--conda-testbed','--miniconda-testbed'],
            capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,2)
        self.assertIn('not allowed with argument',result.stderr)

    def test_path_boundaries(self):
        self.assertEqual(source_path(PREFIX+'/tornado/gen.py'),'tornado/gen.py')
        for path in (PREFIX+'-other/file',PREFIX+'/../file',PREFIX+'/.git/config',
                     PREFIX+'//file','/etc/passwd'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):source_path(path)

    def test_only_initial_shell_root_is_adapted(self):
        command='cd '+PREFIX+' && python -c "print(1)"'
        actions=preflight(call('execute_bash',{'command':command}))
        self.assertEqual(actions[0]['command'],'cd /workspace && python -c "print(1)"')
        for args in ({'command':'pwd'},{'command':command,'is_input':True},
                     {'command':command+'; cat '+PREFIX+'/file'}):
            with self.assertRaises(ValueError):preflight(call('execute_bash',args))

    def test_unknown_editor_action_rejected(self):
        with self.assertRaises(ValueError):
            preflight(call('str_replace_editor',{'command':'undo_edit','path':PREFIX+'/file'}))

    def test_only_exact_root_independent_version_command(self):
        result=preflight(call('execute_bash',{'command':'python --version'}))
        self.assertEqual(result,[{'index':0,'kind':'shell','command':'python --version'}])
        for command in ('python --version; pwd','python --version && pwd','python -V',' python --version'):
            with self.subTest(command=command),self.assertRaises(ValueError):
                preflight(call('execute_bash',{'command':command}))

    def test_thought_content_not_exported_as_an_action(self):
        actions=preflight(call('think',{'thought':'untrusted teacher reasoning'}))
        self.assertEqual(actions,[{'index':0,'kind':'think'}])

class ExplicitReplayProfileTests(unittest.TestCase):
    def profile(self):
        from scripts.replay_tornado_teacher import INSTANCE,TRACE,IMAGE
        return {'instance_id':INSTANCE,'trajectory_id':TRACE,'image':IMAGE,
                'base_commit':'8a9179f2d35e353782aa3611dbdd79c29a5e8185',
                'source_root':PREFIX,'repo':'tornadoweb/tornado','max_tool_calls':40}

    def test_budget_is_explicit_and_bounded(self):
        from scripts.replay_tornado_teacher import validate_profile
        self.assertEqual(validate_profile(self.profile())['max_tool_calls'],40)
        for value in (True,0,101,40.0):
            p=self.profile();p['max_tool_calls']=value
            with self.assertRaises(ValueError):validate_profile(p)

    def test_identity_and_root_mismatches_reject(self):
        from scripts.replay_tornado_teacher import validate_profile
        for key,value in (('image','latest'),('repo','other/repo'),
                          ('source_root','/workspace/../tmp'),('trajectory_id','-'*36)):
            p=self.profile();p[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):validate_profile(p)

    def test_alternate_root_is_mapped_consistently(self):
        prefix='/workspace/example__repo__2.0'
        self.assertEqual(source_path(prefix+'/src/a.py',prefix),'src/a.py')
        result=preflight(call('execute_bash',{'command':'cd '+prefix+' && pwd'}),prefix)
        self.assertEqual(result[0]['command'],'cd /workspace && pwd')

    def test_numeric_issue_identity_remains_repo_bound(self):
        from scripts.replay_source_teacher import validate_profile
        profile=self.profile()
        profile.update(repo='biolink/biolink-model-toolkit',
                       instance_id='biolink__biolink-model-toolkit-172')
        self.assertEqual(validate_profile(profile)['instance_id'],profile['instance_id'])
        for suffix in ('0','-1','172-extra','../172'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                validate_profile({**profile,'instance_id':'biolink__biolink-model-toolkit-'+suffix})


class StandaloneSourceGrepTests(unittest.TestCase):
    def test_identifier_search_preserves_arguments_and_observations(self):
        import shlex
        import subprocess
        import tempfile
        from pathlib import Path
        from scripts.replay_source_teacher import preflight as source_preflight
        prefix='/workspace/example__repo__1.0'
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'source.py'
            path.write_text('def target_name():\n    pass\n# target_name\n')
            for pattern in ('target_name','absent_name'):
                for quote in ('', '"', "'"):
                    command=f'grep -n {quote}{pattern}{quote} {prefix}/src/source.py'
                    action=source_preflight(call('execute_bash',{'command':command}),prefix)[0]
                    before=shlex.split(command);after=shlex.split(action['command'])
                    self.assertEqual(before[:-1],after[:-1])
                    self.assertEqual(after[-1],'/workspace/src/source.py')
                    before[-1]=after[-1]=str(path)
                    old=subprocess.run(before,capture_output=True,timeout=5)
                    new=subprocess.run(after,capture_output=True,timeout=5)
                    self.assertEqual((old.returncode,old.stdout,old.stderr),
                                     (new.returncode,new.stdout,new.stderr))
                    self.assertEqual(new.returncode,0 if pattern=='target_name' else 1)

    def test_unsupported_shell_and_path_forms_reject(self):
        from scripts.replay_source_teacher import preflight as source_preflight
        prefix='/workspace/example__repo__1.0'
        valid=f'grep -n "target_name" {prefix}/src/source.py'
        commands=[valid+'; pwd',valid+' && pwd',valid+' | cat',valid+' > /tmp/output',
                  valid+'\n',valid+' '+prefix+'/second.py',
                  f'grep -n "$(pwd)" {prefix}/src/source.py',
                  f'grep -n "target.*" {prefix}/src/source.py',
                  f'grep -n "target_name\' {prefix}/src/source.py',
                  f'grep -n target_name {prefix}-other/source.py',
                  f'grep -n target_name {prefix}/../source.py',
                  f'grep -n target_name {prefix}/.git/config',
                  f'grep -n target_name {prefix}',
                  f'grep -rn target_name {prefix}/src/source.py']
        for command in commands:
            with self.subTest(command=command),self.assertRaises(ValueError):
                source_preflight(call('execute_bash',{'command':command}),prefix)
        with self.assertRaises(ValueError):
            source_preflight(call('execute_bash',{'command':valid,'is_input':True}),prefix)


class ExplicitSourceTimeoutTests(unittest.TestCase):
    def test_equivalent_timeout_preserves_command_and_records_source_intent(self):
        from scripts.replay_source_teacher import preflight as source_preflight
        prefix = '/workspace/example__repo__1.0'
        args = {'command': 'cd '+prefix+' && python debug_test.py', 'timeout': 30}
        original = dict(args)
        result = source_preflight(call('execute_bash', args), prefix)
        self.assertEqual(args, original)
        self.assertEqual(result, [{'index': 0, 'kind': 'shell',
                                  'command': 'cd /workspace && python debug_test.py',
                                  'source_timeout_seconds': 30}])

    def test_non_equivalent_or_ambiguous_timeouts_reject(self):
        from scripts.replay_source_teacher import preflight as source_preflight
        prefix = '/workspace/example__repo__1.0'
        for timeout in (None, True, 0, -1, 29, 31, 60, 30.0, '30'):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                source_preflight(call('execute_bash', {
                    'command': 'cd '+prefix+' && pwd', 'timeout': timeout}), prefix)
        for args in ({'command': None}, {'command': [], 'timeout': 30},
                     {'command': 'python --version', 'timeout': 30, 'is_input': True}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                source_preflight(call('execute_bash', args), prefix)


if __name__=='__main__':unittest.main()
