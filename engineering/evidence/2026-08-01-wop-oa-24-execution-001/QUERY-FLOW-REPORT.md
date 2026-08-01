# Query Flow Report

`zeus mission <projection>` → CLI controller → Mission Knowledge Model resolver
→ EMM-bound MKM and roadmap validation → Capability Registry validation →
context-local projection → human-readable renderer.

No controller-owned state or alternate authority is introduced. The OA-24
correction reuses the validated `(value, by_id, capabilities)` context within a
single request and preserves the existing structured result and digest fields.
