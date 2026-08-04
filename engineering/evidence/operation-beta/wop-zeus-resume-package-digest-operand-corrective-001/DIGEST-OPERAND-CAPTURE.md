# Digest Operand Capture

The incorrect published expression was at
`scripts/lib/emp/admission_supersession.py:141`:

```python
package_digest = predecessor.get("package_digest") or stage1_transaction.get("package_digest")
if stage1_transaction.get("package_digest") and package_digest != stage1_transaction.get("package_digest"):
```

Its incorrect left operand was the generic projected admission field
`predecessor.get("package_digest")`; its right operand was the immutable Stage
1 transaction field. The two fields were treated as equivalent without first
establishing their semantic role.

The corrected capture is explicit:

```text
expected = authoritative Stage 1 transaction.package_digest
observed = each admission stage1_package_digest/package_digest/nested package binding
```

Failures report `expected`, `observed`, and the exact binding field. No
permissive fallback accepts an unknown relationship.
