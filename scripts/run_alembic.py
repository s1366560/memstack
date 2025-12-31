#!/usr/bin/env python3
"""Wrapper script to run Alembic commands."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from alembic.config import CommandLine

if __name__ == "__main__":
    CommandLine().main(argv=sys.argv[1:])
