# Runtime Schema Migration Report

Legacy schema-v2 records may pass through hydration before lifecycle projection checks. Hydration persists only derived projection fields and provenance; the existing migration then advances the record to schema 3 without changing transaction, WOP, registration, package, or receipt identities.
