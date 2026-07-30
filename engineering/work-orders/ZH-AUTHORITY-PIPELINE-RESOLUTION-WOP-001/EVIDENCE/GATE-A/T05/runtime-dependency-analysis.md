# T05 Runtime Dependency Analysis

## Before T05

```text
progressive_lifecycle (Layer 3)
  -> progressive_gate (Layers 1 and 2)
       -> progressive_oa (compatibility)
            -> progressive_gate (lazy compatibility delegation)
```

The `progressive_gate -> progressive_oa` edge violated the compatibility
boundary and formed a conceptual runtime/adapter cycle.

## After T05

```text
progressive_lifecycle (Layer 3)
  -> progressive_gate (Layers 1 and 2)
       -> progressive_runtime_support (foundational shared utility)

progressive_oa (compatibility) -> progressive_gate
oa02_lifecycle (compatibility) -> progressive_lifecycle
```

Static validation reports:

- runtime edges:
  `progressive_gate -> []`,
  `progressive_lifecycle -> [progressive_gate]`;
- compatibility consumption:
  `progressive_oa -> progressive_gate`,
  `oa02_lifecycle -> progressive_lifecycle`;
- no upward edge;
- no runtime cycle;
- no runtime-to-compatibility edge;
- no foundational back-edge; and
- no projection authority definition.

`progressive_gate.py` contains both accepted Layer 1 and Layer 2 surfaces, as
frozen during T04. T05 does not split or redesign that module.

