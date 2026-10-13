#!/usr/bin/env python3
"""Git textconv: decode EnScript for display without changing archived blobs."""
import sys
from pathlib import Path
from inspect_sources import decode_source
sys.stdout.write(decode_source(Path(sys.argv[1]).read_bytes()))
