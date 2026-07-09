#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

if len(sys.argv) != 3:
    raise SystemExit("Usage: repair_yaml_header.py <file> <body-heading>")

path = Path(sys.argv[1])
heading = sys.argv[2]

text = path.read_text()
start = text.find(heading)
if start == -1:
    raise SystemExit(f"Could not find body heading: {heading}")

body = text[start:]

# This script only validates that a caller-supplied file already has a YAML
# header. Document-specific header repair still happens through controlled input.
parts = text.split("---", 2)
if len(parts) >= 3:
    try:
        yaml.safe_load(parts[1])
        print(f"PASS: YAML valid: {path}")
        raise SystemExit(0)
    except Exception as e:
        print(f"FAIL: YAML invalid: {path}")
        print(e)
        raise SystemExit(1)

raise SystemExit(f"FAIL: Missing YAML front matter: {path}")
