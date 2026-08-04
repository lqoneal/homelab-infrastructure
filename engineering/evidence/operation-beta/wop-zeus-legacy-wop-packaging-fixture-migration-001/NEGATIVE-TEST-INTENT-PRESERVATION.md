# Negative Test Intent Preservation

Malformed DOCX still tests document parsing. Conflicting WOP IDs still test
metadata conflict detection. Manifest and promotion tests still inject exactly
one failure at their original boundary. The supersession test now changes only
one canonical scope value. No negative case passes through permissive defaults.
