#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

if len(sys.argv) != 2:
    raise SystemExit("Usage: repair_yaml_header.py <markdown-file>")

p = Path(sys.argv[1])

if not p.exists():
    raise SystemExit(f"FAIL: file not found: {p}")

text = p.read_text()

if not text.startswith("---"):
    raise SystemExit("FAIL: missing YAML front matter")

parts = text.split("---", 2)

if len(parts) < 3:
    raise SystemExit("FAIL: missing closing YAML delimiter")

raw_header = parts[1]
body = parts[2].lstrip("\n")

lines = raw_header.splitlines()
fixed = []
current_key = None

list_keys = {"related_documents", "tags", "implements", "governed_by"}

for line in lines:
    stripped = line.strip()

    if not stripped:
        fixed.append(line)
        continue

    if stripped.endswith(":"):
        current_key = stripped[:-1]
        fixed.append(stripped)
        continue

    if stripped.startswith("* "):
        if current_key in list_keys:
            fixed.append(f"  - {stripped[2:]}")
        else:
            fixed.append(line)
        continue

    if stripped.startswith("- "):
        if current_key in list_keys and not line.startswith("  - "):
            fixed.append(f"  - {stripped[2:]}")
        else:
            fixed.append(line)
        continue

    current_key = None
    fixed.append(line)

new_header = "\n".join(fixed).strip() + "\n"

# Validate before writing.
yaml.safe_load(new_header)

p.write_text("---\n" + new_header + "---\n\n" + body)

print(f"REPAIRED: {p}")
