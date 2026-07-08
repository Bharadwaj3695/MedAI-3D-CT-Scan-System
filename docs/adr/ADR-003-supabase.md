# ADR-003: Selection of Supabase for Database & Storage

* **Date**: June 30, 2026
* **Status**: Approved

## Context
We need a database to store user profiles, scan metadata, AI predictions, and clinical reports. We also need an object storage solution to host large 3D CT scans (up to 150MB each).

We considered:
1. **Self-hosted PostgreSQL + AWS S3**: High control, but requires significant DevOps overhead to configure backups, connection pools, and access policies.
2. **Supabase**: An open-source Firebase alternative providing PostgreSQL, GoTrue Auth, and S3-compatible Object Storage out of the box.

## Decision
We chose **Supabase** as our backend-as-a-service provider.

## Consequences
* **Positives**:
  - Greatly accelerates development by combining Auth, Database, and Storage into a single platform.
  - PostgreSQL support allows complex relational queries and JSONB columns (ideal for storing structured AI results).
  - Row-Level Security (RLS) policies secure data directly at the database level, assisting in HIPAA compliance.
* **Negatives**:
  - Ties us to the Supabase ecosystem, though the underlying database remains standard PostgreSQL, allowing for future migration if necessary.
