"""Offline inspection CLI. Results go to stdout; inputs are never modified."""

import argparse
from dataclasses import asdict
from pathlib import Path
import sys
import zipfile

from .archive import inspect_zip
from .artifacts import canonical_json, inventory, load_json, verify
from .contracts import Event, Kind, replay
from .splits import validate_splits


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m zenithsync")
    commands = parser.add_subparsers(dest="command", required=True)
    intake = commands.add_parser("inventory")
    intake.add_argument("root", type=Path)
    intake.add_argument("--kind", required=True, choices=["model", "harness", "candidate", "fixture"])
    intake.add_argument("--source", required=True)
    intake.add_argument("--revision", required=True)
    check = commands.add_parser("verify")
    check.add_argument("root", type=Path)
    check.add_argument("manifest", type=Path)
    split = commands.add_parser("check-splits")
    split.add_argument("manifest", type=Path)
    events = commands.add_parser("replay")
    events.add_argument("events", type=Path)
    archive = commands.add_parser("check-zip")
    archive.add_argument("archive", type=Path)
    archive.add_argument("--max-bytes", required=True, type=int)
    archive.add_argument("--max-entries", required=True, type=int)
    args = parser.parse_args()
    try:
        if args.command == "inventory":
            result = inventory(args.root, kind=args.kind, source=args.source, revision=args.revision)
        elif args.command == "verify":
            verify(args.root, load_json(args.manifest))
            result = {"byte_identity": "verified", "publisher_authenticity": "not_established"}
        elif args.command == "check-splits":
            result = validate_splits(load_json(args.manifest))
        elif args.command == "replay":
            records = load_json(args.events)
            if not isinstance(records, list):
                raise ValueError("event file must be a JSON array")
            parsed = []
            for record in records:
                if not isinstance(record, dict) or "kind" not in record:
                    raise ValueError("invalid event record")
                parsed.append(Event(**{**record, "kind": Kind(record["kind"])}))
            result = asdict(replay(parsed))
        else:
            result = inspect_zip(args.archive, max_bytes=args.max_bytes, max_entries=args.max_entries)
        sys.stdout.buffer.write(canonical_json(result))
        return 0
    except (ValueError, TypeError, OSError, zipfile.BadZipFile, NotImplementedError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
