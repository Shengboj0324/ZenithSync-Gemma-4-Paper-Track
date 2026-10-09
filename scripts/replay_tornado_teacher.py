"""Compatibility entry point for the original Tornado replay profile."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.replay_source_teacher import (
    IMAGE, INSTANCE, PREFIX, TRACE, main, preflight, source_path, validate_profile,
)

if __name__=='__main__':main()
