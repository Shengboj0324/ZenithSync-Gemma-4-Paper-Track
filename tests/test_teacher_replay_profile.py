import unittest
from scripts.replay_tornado_teacher import PREFIX,preflight,source_path


def call(name,arguments):
    return [{'tool_calls':[{'function':{'name':name,'arguments':arguments}}]}]


class TeacherReplayProfileTests(unittest.TestCase):
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


if __name__=='__main__':unittest.main()
