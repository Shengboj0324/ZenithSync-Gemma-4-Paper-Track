"""Compatibility entry point; use grade_replayed_patch.py for new workflows."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.grade_replayed_patch import main

if __name__=='__main__':main()
