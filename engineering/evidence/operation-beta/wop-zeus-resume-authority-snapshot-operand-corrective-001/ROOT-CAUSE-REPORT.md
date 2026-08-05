# Root Cause Report

Resume conflated a generic admission projection field with the authoritative authority source. The first failing resolution point was the direct equality check in `scripts/lib/emp/admission_supersession.py` inside `resolve_for_resume`. Receipt-backed authority was available but not consulted when the generic field was absent.

