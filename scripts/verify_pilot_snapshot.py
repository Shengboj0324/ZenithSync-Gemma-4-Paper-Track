"""Inspect the official pilot snapshot in Linux without executing repository code."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record,load_json,verify


def run(*command):
    return subprocess.check_output(command,text=True,timeout=90).strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--image",required=True)
    parser.add_argument("--upstream-commit",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    manifest=load_json(args.manifest)
    verify(args.bundle,manifest)
    task=json.loads((args.bundle/"tasks.jsonl").read_text())
    upstream=load_json(args.upstream_commit)
    if upstream["sha"]!=task["base_commit"]:
        raise ValueError("upstream evidence refers to a different task commit")
    snapshot=args.bundle/"snapshots"/(task["instance_id"]+".tgz")
    image=run("docker","image","inspect",args.image,"--format","{{.Id}}")
    container=run("docker","create","--platform","linux/amd64","--network","none","--memory","4g","--cpus","2",
                  "--pids-limit","256",image,"sleep","600")
    result={}
    try:
        run("docker","start",container)
        config=json.loads(run("docker","inspect",container))[0]
        host=config["HostConfig"]
        if host["NetworkMode"]!="none" or config["Mounts"]:
            raise RuntimeError("sandbox isolation mismatch")
        run("docker","cp",str(snapshot),container+":/tmp/pilot.tgz")
        run("docker","exec",container,"mkdir","-p","/workspace")
        run("docker","exec",container,"tar","-xzf","/tmp/pilot.tgz","-C","/workspace","--no-same-owner")
        head=run("docker","exec","-w","/workspace",container,"git","rev-parse","HEAD")
        tree=run("docker","exec","-w","/workspace",container,"git","rev-parse","HEAD^{tree}")
        if tree!=upstream["tree_sha"]:
            raise RuntimeError("snapshot source tree differs from the upstream task commit")
        run("docker","exec","-w","/workspace",container,"git","diff","--no-ext-diff",
            "--no-textconv","--exit-code","HEAD","--")
        code="""import ast,json
from pathlib import Path
roots=[p for p in [Path('/workspace/requests'),Path('/workspace/src/requests')] if p.is_dir()]
if len(roots)!=1: raise RuntimeError('ambiguous package directory')
files=sorted(roots[0].rglob('*.py'))
if not files: raise RuntimeError('no package sources')
for path in files: ast.parse(path.read_bytes(),filename=str(path))
print(json.dumps({'python_files_parsed':len(files),'package_path':str(roots[0])}))
"""
        result=json.loads(run("docker","exec",container,"python","-c",code))
        result.update({"snapshot_head":head,"advertised_base_commit":task["base_commit"],
                       "source_tree":tree,"upstream_tree_match":True,
                       "tracked_worktree_clean":True,"network":"none","host_mounts":0,
                       "memory_bytes":host["Memory"],"nano_cpus":host["NanoCpus"]})
        verify(args.bundle,manifest)
    finally:
        run("docker","rm","-f",container)
    receipt={"schema_version":1,"status":"linux_snapshot_checks_passed",
             "timestamp_utc":datetime.now(timezone.utc).isoformat(),"image_id":image,
             "verifier":file_record(Path(__file__)),"manifest":file_record(args.manifest),
             "upstream_commit_evidence":file_record(args.upstream_commit),
             "result":result,"container_removed":True,
             "scope":"snapshot commit and package syntax; no dependency install, tests or model"}
    (args.output/"receipt.json").write_bytes(canonical_json(receipt))
    print("Linux snapshot commit and syntax checks passed; temporary container removed.")


if __name__=="__main__":
    main()
