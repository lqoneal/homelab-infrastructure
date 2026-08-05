# Stage 2 / Stage 4 Reconciliation

Stage 2 validates EOS against published `main` and reports candidate parity as `UNPUBLISHED_CANDIDATE`. Stage 4 operational-state and checkpoint checks use the same expected published baseline. Non-synchronization checks continue to run unchanged. Candidate-to-EOS synchronization is explicitly prohibited.
