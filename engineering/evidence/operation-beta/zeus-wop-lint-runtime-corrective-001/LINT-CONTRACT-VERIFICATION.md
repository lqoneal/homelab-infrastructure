# Lint Contract Verification

The valid staged v2.1 WOP now returns exit code 0 for human and JSON lint.
Repeated JSON lint results are equivalent after parsing. Missing metadata
returns exit code 78 with every missing field in `lint.issues`; invalid UTF-8
input returns a controlled issue and no traceback. Lint does not package,
register, create provenance, initialize runtime, or alter its source.
