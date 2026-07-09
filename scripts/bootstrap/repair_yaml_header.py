#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

HEADERS = {
    "TPL-0001": {
        "path": "docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md",
        "heading": "# Engineering Work Order Template",
        "header": """---
document_id: TPL-0001
title: Engineering Work Order Template
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-09
phase: Governance Bootstrap
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0003
  - PROC-0001
tags:
  - governance
  - template
  - work-order
  - execution
  - engineering-operating-system
---

"""
    },
    "TPL-0002": {
        "path": "docs/templates/TPL-0002-ENGINEERING_COMPLETION_REPORT_TEMPLATE.md",
        "heading": "# Engineering Completion Report Template",
        "header": """---
document_id: TPL-0002
title: Engineering Completion Report Template
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-09
phase: Governance Bootstrap
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0003
  - PROC-0001
  - TPL-0001
tags:
  - governance
  - template
  - completion-report
  - evidence
  - engineering-operating-system
---

"""
    },
    "TPL-0003": {
        "path": "docs/templates/TPL-0003-ENGINEERING_EVIDENCE_PACKAGE_TEMPLATE.md",
        "heading": "# Engineering Evidence Package Template",
        "header": """---
document_id: TPL-0003
title: Engineering Evidence Package Template
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-09
phase: Governance Bootstrap
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0003
  - PROC-0001
  - TPL-0001
  - TPL-0002
tags:
  - governance
  - template
  - evidence-package
  - traceability
  - engineering-operating-system
---

"""
    },
}

if len(sys.argv) != 2 or sys.argv[1] not in HEADERS:
    valid = ", ".join(sorted(HEADERS))
    raise SystemExit(f"Usage: repair_yaml_header.py <document_id>\nValid: {valid}")

doc = HEADERS[sys.argv[1]]
p = Path(doc["path"])
text = p.read_text()

start = text.find(doc["heading"])
if start == -1:
    raise SystemExit(f"Could not find body heading: {doc['heading']}")

body = text[start:]
p.write_text(doc["header"] + body)

# Validate repaired YAML.
parts = p.read_text().split("---", 2)
yaml.safe_load(parts[1])

print(f"REPAIRED: {sys.argv[1]} YAML header")
