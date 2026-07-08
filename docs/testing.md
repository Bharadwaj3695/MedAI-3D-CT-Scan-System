# Testing Strategy

This document outlines the testing framework and strategy for the **MedAI-3D-CT-Scan-System** to ensure code reliability, security, and feature correctness.

---

## 1. Frontend Testing

The frontend uses **Vitest** for unit and component testing, and **Playwright** for End-to-End (E2E) integration testing.

### Unit & Component Tests (Vitest)
Unit tests focus on helper functions, utility classes, and rendering UI components in isolation:
- Run tests:
  ```bash
  cd frontend
  npm run test
  ```
- Test areas:
  - Component rendering of `StatusBadge`, `StatsCard`, and `EmptyState`.
  - Date and string formatting utilities.

### End-to-End (E2E) Tests (Playwright)
Playwright simulates real user interactions in headless browsers (Chromium, Firefox, WebKit) to verify critical user journeys:
- Run tests:
  ```bash
  cd frontend
  npx playwright test
  ```
- Critical paths tested:
  - **Authentication**: Signup, login, session recovery, and logout.
  - **Scan Upload**: Dragging a file, validating types, uploading, and ensuring progress animations render.
  - **Results Page**: Verifying Grad-CAM canvas rendering, tab switching, and AI chatbot responses.

---

## 2. Backend Testing

The backend uses **pytest** to test API endpoints and service classes.

### Unit & Integration Tests
We mock external services (such as Supabase Storage and database queries) to isolate backend logic:
- Run tests:
  ```bash
  pytest backend/test/
  ```
- Test areas:
  - File size and extension validation.
  - Exception mapping (ensuring `AppException` is correctly caught and converted to JSONResponse).
  - JWT token generation and signature verification.
  - Mocking PyTorch model inference outputs to verify database insertion logic.
