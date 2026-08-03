# Baseline Identity Mismatch Report

The staged ZDCL-02 source declared `homelab`; the runtime binding is the
repository `/data/engineering/repositories/homelab` with remote
`git@github.com:lqoneal/homelab-infrastructure.git`, repository ID
`homelab-6bd83f9079d6fc57`, and fingerprint
`6bd83f9079d6fc5780ca2cb9a93060778a899cd97e82ef3d708f91a42dbda02d`.
The source digest remains
`6567d9eaac47bea91b0346731cc3bac91566ccfa52cb4e2e6d86f3da61ef5334`.

The mismatch was a representation mismatch, not evidence of a foreign
repository. No staged source was submitted by this corrective.
