"""Audit a completed native replay's recorded observations without executing it."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zenithsync.artifacts import canonical_json,file_record,load_json
from zenithsync.replay_observations import audit_observations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    paths=[args.attempt/name for name in ('receipt.json','events.json','submitted.patch')]
    paths += [Path(__file__),ROOT/'zenithsync/replay_observations.py']
    inputs={str(p):file_record(p) for p in paths}
    receipt=load_json(args.attempt/'receipt.json')
    if (receipt['status']!='replayed_not_graded' or receipt['cleanup']['removed'] is not True
            or receipt['source_observations_reused'] is not False
            or receipt['patch']!=inputs[str(args.attempt/'submitted.patch')]):
        raise ValueError('Completed fresh-observation replay required')
    report=audit_observations(load_json(args.attempt/'events.json'))
    charged=sum(count for tool,count in report['tool_counts'].items() if tool!='submit_patch')
    if charged!=receipt['tool_calls']:
        raise ValueError('Recorded charged calls differ from replay receipt')
    if any(file_record(Path(p))!=identity for p,identity in inputs.items()):
        raise ValueError('Observation audit inputs changed')
    report.update(inputs=inputs,trajectory_id=receipt['trajectory_id'],charged_calls=charged)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'report.json').write_bytes(canonical_json(report))
    print({k:report[k] for k in ('charged_calls','status_counts','explicitly_truncated_calls',
                                  'truncation_unspecified_calls','nonzero_exit_calls')})


if __name__=='__main__':main()
