# Source and Package Digest Report

Recovery continues to verify receipt-bound source digest and package digest. For directory-backed packages it also recomputes the package tree digest. A mismatch raises `PACKAGE_DIGEST_MISMATCH` or `SOURCE_DIGEST_MISMATCH`; hydration never repairs a digest.
