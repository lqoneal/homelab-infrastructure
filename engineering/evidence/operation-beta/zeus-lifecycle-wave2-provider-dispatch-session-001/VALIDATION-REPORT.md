# Validation Report

CONTROLLED_DOCUMENT_VALIDATION=PASS
SEMANTIC_VALIDATION=PASS
REGISTRY_VALIDATION=PASS
ASSURANCE_VALIDATION=PASS
SCHEMA_VALIDATION=PASS
ZEUS_PLATFORM_VALIDATION=PASS
ZEUS_STATUS_RECONCILIATION=PASS
OPERATION_BETA_VALIDATION=PASS
INTEGRATED_VALIDATION=PASS
REPOSITORY_EOS_VALIDATION=PASS
GIT_DIFF_CHECK=PASS
GIT_CACHED_DIFF_CHECK=PASS

The complete validator invocation without the unrelated synchronization catalog
was:
python3 scripts/validate_controlled_documents.py --semantic-all --conformance --assurance
It passed 3808 checks. engctl validate homelab and engctl eos sync-validate
homelab also passed. The additive synchronization catalog was separately run
and classified as pre-existing unrelated fingerprint drift; it was not
weakened or modified.
