# ADR-002: Selection of React + Vite for Frontend

* **Date**: June 30, 2026
* **Status**: Approved

## Context
The frontend needs to handle heavy client-side rendering (e.g., drawing 2D CT cross-sections and Grad-CAM overlays on HTML5 Canvases) and maintain state for an AI chatbot.

We considered:
1. **Next.js (SSR)**: Excellent for SEO, but adds unnecessary server-side complexity since our app is a private, authenticated medical dashboard.
2. **React SPA (Vite)**: Lightweight, fast build times, and compiles to static assets that can be easily hosted on a CDN.

## Decision
We chose **React** compiled with **Vite** as our frontend stack.

## Consequences
* **Positives**:
  - Extremely fast Hot Module Replacement (HMR) during development.
  - Static build output (`dist/`) can be hosted cheaply and securely on Vercel, Netlify, or AWS S3.
  - Strong ecosystem of UI libraries (shadcn/ui, Tailwind CSS) and data fetching tools (React Query).
* **Negatives**:
  - Client-side routing requires configuring fallback redirects on the hosting provider to prevent 404 errors on page refresh.
