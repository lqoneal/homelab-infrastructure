# Packaging Corrective Report

Implemented in `scripts/lib/emp/wop_packaging.py`:

1. Track active metadata heading level.
2. Preserve nested headings under the active section.
3. Flush at peer or higher-level headings regardless of whether the heading is
   a recognized metadata key.
4. Preserve existing inline-label and list normalization behavior.

Added focused tests in `scripts/tests/test-wop-packaging.py` for nested/peer
headings and canonical package field-boundary preservation.

No runtime, authority, admission, provider, EOS, or publication behavior was
changed.
