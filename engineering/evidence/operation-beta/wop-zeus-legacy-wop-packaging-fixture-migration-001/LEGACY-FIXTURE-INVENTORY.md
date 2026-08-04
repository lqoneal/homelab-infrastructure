# Legacy Fixture Inventory

`test-wop-packaging.py` contained seven legacy dependencies: the shared Markdown
fixture, the boundary parser fixture, an external DOCX fixture, table metadata,
invalid-document setup, atomic-promotion setup, replay setup, and source-change
supersession setup. Positive inputs depended on the former 14-field shape.

The external obsolete DOCX dependency was replaced by the canonical DOCX
factory; negative malformed-DOCX coverage remains unchanged.
