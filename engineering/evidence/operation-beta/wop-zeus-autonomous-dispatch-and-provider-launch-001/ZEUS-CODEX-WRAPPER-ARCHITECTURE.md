# Zeus Codex Wrapper Architecture

The provider path is `Zeus lifecycle -> CodexWrapper -> engctl codex -> Codex`.
Zeus owns context, identity, process group, journal, stop/resume, and receipts;
engctl supplies the lower-level launch service. The adapter is provider-neutral
and refuses to launch without one uniquely qualified provider.
