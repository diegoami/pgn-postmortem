#!/usr/bin/env python3
"""Compatibility wrapper - see pgn_postmortem/markdown_site.py (or `pgn-postmortem --help`)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pgn_postmortem.markdown_site import main  # noqa: E402

if __name__ == "__main__":
    main()
