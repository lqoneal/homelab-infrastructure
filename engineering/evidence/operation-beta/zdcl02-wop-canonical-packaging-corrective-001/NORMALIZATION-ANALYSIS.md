# Normalization Analysis

Normalization remains deterministic and source-fact-only:

- list fields split only on existing comma/semicolon/newline rules;
- YAML list values remain lists;
- scalar values remain scalar values;
- no authority, scope, dependency, effect, or baseline is invented;
- source digest remains the package identity input;
- source preservation remains byte-verified.

The only behavioral correction is section termination at peer/higher-level
headings. Existing flat authoring fixtures remain compatible.
