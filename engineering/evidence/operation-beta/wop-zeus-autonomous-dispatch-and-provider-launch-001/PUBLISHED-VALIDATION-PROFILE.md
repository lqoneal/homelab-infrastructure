# Published Validation Profile

Published validation is strict. `main` must equal `origin/main`; EOS state, active checkpoint, operational state, and persistence projections must all represent that exact commit. Any stale, ahead, rewound, dirty, detached, or ambiguous state fails.
