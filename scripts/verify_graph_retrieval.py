"""Compare official retrieval on real pilot assets with float64 cosine reference."""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from zenithsync.artifacts import canonical_json, file_record, load_json, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import numpy as np
    from swegemma.graph import get_similar_nodes, retrieval_utils
    from zenithsync.task_intake import AGENT_FIELDS
    import json

    manifest = load_json(args.manifest)
    verify(args.bundle, manifest)
    tasks = [json.loads(line) for line in (args.bundle / "tasks.jsonl").read_text().splitlines()]
    if len(tasks) != 1 or set(tasks[0]) != set(AGENT_FIELDS):
        raise ValueError("expected one projected pilot task")
    task = tasks[0]
    embedding_path = next((args.bundle / "embeddings").glob("*.npz"))
    with np.load(embedding_path, allow_pickle=False) as data:
        vectors = {name: [float(x) for x in data[name]] for name in data.files}
    names = sorted(vectors)
    norms = {name: math.sqrt(math.fsum(x*x for x in value)) for name,value in vectors.items()}
    if any(not math.isfinite(norm) or norm <= 0 for norm in norms.values()):
        raise ValueError("nonfinite or zero embedding norm")
    kwargs = dict(repo_name=task["repo"], base_commit=task["base_commit"],
                  graph_dir=str((args.bundle / "graphs").resolve()),
                  embeddings_dir=str((args.bundle / "embeddings").resolve()),
                  use_local_storage=True, use_memoization=False)
    records = []
    tolerance = 1e-5  # Explicit absolute comparison tolerance; not an accuracy metric.
    for query in [names[0], names[len(names)//2], names[-1]]:
        reference = {name: math.fsum(a*b for a,b in zip(vectors[query],vectors[name], strict=True))
                     / (norms[query]*norms[name]) for name in names if name != query}
        expected = sorted(reference, key=lambda name: (-reference[name], name))[:5]
        actual = get_similar_nodes(node=query, k=5, **kwargs)
        returned = [item["node_name"] for item in actual]
        if len(returned) != 5 or len(set(returned)) != 5 or query in returned:
            raise ValueError("invalid retrieval cardinality, duplication or self match")
        errors = []
        for item in actual:
            name = item["node_name"]
            score = float(item["similarity"])
            error = abs(score-reference[name])
            if not math.isfinite(score) or error > tolerance:
                raise ValueError("official cosine score differs from float64 reference")
            if reference[name] < reference[expected[-1]] - tolerance:
                raise ValueError("retrieval missed a materially closer neighbor")
            errors.append(error)
        if any(float(a["similarity"]) < float(b["similarity"])
               for a,b in zip(actual,actual[1:])):
            raise ValueError("retrieval results are not score ordered")
        records.append({"query":query,"returned":returned,"reference_top5":expected,
                        "exact_rank_agreement":returned==expected,"max_score_error":max(errors)})
    for k in [0,-1]:
        try:
            get_similar_nodes(node=names[0],k=k,**kwargs)
        except ValueError:
            pass
        else:
            raise ValueError("invalid neighbor count accepted")
    verify(args.bundle,manifest)
    receipt = {"schema_version":1,"status":"official_retrieval_checks_passed",
               "timestamp_utc":datetime.now(timezone.utc).isoformat(),
               "swegemma_version":version("swegemma"),"numpy_version":version("numpy"),
               "verifier":file_record(Path(__file__)),
               "official_retrieval_source":file_record(Path(retrieval_utils.__file__)),
               "bundle_manifest":file_record(args.manifest),"queries":records,
               "absolute_tolerance":tolerance,"invalid_k_rejections":2,
               "scope":"three deterministic real-asset queries; no model or repair performance"}
    (args.output/"receipt.json").write_bytes(canonical_json(receipt))
    print("Official retrieval matches independent cosine checks for all three pilot queries.")


if __name__ == "__main__":
    main()
