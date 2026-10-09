"""Compare the original Tornado gen_test module across source sanitization."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_source_snapshot import run_image
from zenithsync.artifacts import canonical_json,file_record

CHILD = r'''
import json, pathlib, unittest
class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.outcomes = {}
    def record(self,test,status):
        if test.id() in self.outcomes:
            raise RuntimeError('Duplicate test identity')
        self.outcomes[test.id()] = status
    def addSuccess(self,test):
        super().addSuccess(test); self.record(test,'passed')
    def addFailure(self,test,err):
        super().addFailure(test,err); self.record(test,'failed')
    def addError(self,test,err):
        super().addError(test,err); self.record(test,'error')
    def addSkip(self,test,reason):
        super().addSkip(test,reason); self.record(test,'skipped')
suite=unittest.defaultTestLoader.loadTestsFromName('tornado.test.gen_test')
r=unittest.TextTestRunner(resultclass=Result,verbosity=2).run(suite)
if len(r.outcomes)!=r.testsRun or not r.outcomes:
    raise RuntimeError('Incomplete outcome capture')
pathlib.Path('/audit/outcomes.json').write_text(json.dumps(r.outcomes))
raise SystemExit(not r.wasSuccessful())
'''
PROBE = r'''
import json,pathlib,subprocess
pathlib.Path('/audit').mkdir()
run = subprocess.run(['/testbed/.venv/bin/python','-W','ignore','-c',CHILD],
    cwd='/testbed',text=True,capture_output=True,timeout=240)
pathlib.Path('/audit/test.log').write_text(run.stdout+'\n'+run.stderr)
outcomes=json.loads(pathlib.Path('/audit/outcomes.json').read_text())
diff = subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd='/testbed',capture_output=True,timeout=30)
if diff.returncode != 0:
    raise RuntimeError('Repository tests modified tracked source')
pathlib.Path('/audit/runtime.json').write_text(json.dumps({'exit':run.returncode,
    'outcomes':outcomes,'tracked_source_unchanged':True}))
raise SystemExit(run.returncode)
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',required=True)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    outcomes={}
    for role,image in [('original',args.original),('snapshot',args.snapshot)]:
        receipt=run_image(image,args.output/role,probe="CHILD = "+repr(CHILD)+"\n"+PROBE)
        if receipt['returncode'] not in (0,1) or receipt['cleanup_returncode'] != 0 or receipt['state']['OOMKilled']:
            raise RuntimeError('Test execution or cleanup failed')
        outcomes[role]=json.loads((args.output/role/'runtime.json').read_text())
    if outcomes['original'] != outcomes['snapshot']:
        raise RuntimeError('Repository outcomes changed after sanitization')
    report={'status':'passed','case_count':len(outcomes['snapshot']['outcomes']),
            'outcomes_identical':True,'script':file_record(Path(__file__)),
            'scope':'Original repository gen_test module only; no complete test-suite or agent claim',
            'training_approved':False}
    (args.output/'comparison.json').write_bytes(canonical_json(report))
    print(report)


if __name__=='__main__':
    main()
