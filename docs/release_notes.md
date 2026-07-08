# Release Notes & Changelog

This document logs all releases, major updates, and refactoring efforts for the **MedAI-3D-CT-Scan-System**.

---

## v1.1.0 (June 30, 2026) - UI Standardization & Concurrency Fixes

### Added
- Created reusable UI components under `src/components/ui/`:
  - `StatusBadge.tsx`: Displays scan status with consistent Tailwind colors.
  - `StatsCard.tsx`: Standardizes statistics representation on the dashboard.
  - `EmptyState.tsx`: Provides a placeholder for empty lists and modals.
  - `LoadingSkeleton.tsx`: Standardizes loading states across the dashboard, tables, and cards.
- Enhanced `UploadScan.tsx` with a stage-by-stage progress indicator:
  - Progress bar animates smoothly through file validation, uploading, preprocessing, nodule detection, and result saving.
  - Inputs and buttons are disabled during the upload process to prevent double submissions.

### Changed
- Refactored `Dashboard.tsx`, `ScanHistory.tsx`, and `ScanResults.tsx` to use the new reusable UI components.
- Optimized backend event loop concurrency:
  - Converted blocking CPU-bound and I/O-bound route handlers (such as `predict_scan` in `main.py`, exception handlers in `exceptions.py`, and other database-heavy operations) from `async def` to synchronous `def` to ensure they run on FastAPI's external threadpool and do not block the ASGI event loop.

### Fixed
- Resolved a duplicate `useAuth` import in `AdminPanel.tsx` preventing compilation.
- Fixed an unclosed `.map` expression in `Dashboard.tsx` causing syntax errors.
- Resolved type-casting issues in the `icon` prop of `StatsCard` and `EmptyState`.
