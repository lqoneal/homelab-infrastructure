# Repository Transition Classification

`classify_transition` requires current published `main` to descend directly from the terminal baseline, local HEAD to equal `origin/main`, a clean tree, and changed paths within the controlled transition allowlist. Unpublished, dirty, rewound, ambiguous, or unauthorized transitions fail closed.

