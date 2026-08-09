# Worktree Classification

Classification is persisted before staging. The current implementation uses
these dispositions:

| Class | Meaning |
|---|---|
| `MISSION_CANDIDATE` | Path named by a qualified publication manifest. |
| `RELATED_CONTROLLED_DOCUMENT` | Controlled document not independently selected by dirty status. |
| `RELATED_EVIDENCE` | Evidence retained for traceability, not automatically published. |
| `UNRELATED_DIRTY` | Dirty path without candidate authority; preserved and unstaged. |
| `GENERATED_RUNTIME` | Repository-local generated/configuration state excluded by policy. |
| `AMBIGUOUS` / `BLOCKED` | Current path or candidate authority cannot be resolved safely. |

Missing candidate paths, ambiguous classification, changed candidate content,
and unexpected staged paths fail closed.
