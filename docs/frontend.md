# Frontend Architecture

The frontend of the **MedAI-3D-CT-Scan-System** is a Single Page Application (SPA) built using **React 18**, **TypeScript**, and **Vite**. Styling is managed using **Tailwind CSS** and **shadcn/ui** components.

## Directory Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/          # Reusable low-level primitives (Button, Card, StatsCard)
│   │   └── ProtectedRoute.tsx # Route guard for authentication
│   ├── contexts/
│   │   └── AuthContext.tsx # Auth state provider (login, signup, session recovery)
│   ├── hooks/
│   │   └── use-toast.ts # shadcn toast hook
│   ├── pages/           # Page-level components
│   │   ├── Dashboard.tsx
│   │   ├── ScanHistory.tsx
│   │   ├── ScanResults.tsx
│   │   ├── UploadScan.tsx
│   │   └── Landing.tsx
│   ├── services/
│   │   └── auth.service.ts # HTTP wrapper for auth endpoints
│   ├── App.tsx          # Router configuration
│   └── main.tsx         # App entrypoint
```

## Core Patterns

### 1. State Management
- **Authentication State**: Global state (user profile, session tokens, roles) is managed via React Context in `AuthContext.tsx`.
- **Server Cache**: Server state (scans, reports, stats) is managed using **@tanstack/react-query**. This ensures automatic caching, background refetching, and state synchronization without complex Redux boilers.
- **Local UI State**: Handled using standard React `useState` hooks.

### 2. Routing & Route Guarding
- **React Router v6** is used for client-side routing.
- **[ProtectedRoute.tsx](file:///mnt/d/Projects/MedAI-3D-CT-Scan-System/frontend/src/components/ProtectedRoute.tsx)** wraps private routes:
  - If the user is not authenticated, they are redirected to `/login`.
  - If a route requires a specific role (e.g., `/admin` requires `admin`), it checks `userRole` before rendering the children.

### 3. Reusable UI Components
Low-level components are structured around shadcn/ui. We have created specific reusable components to eliminate duplication:
- **[StatusBadge.tsx](file:///mnt/d/Projects/MedAI-3D-CT-Scan-System/frontend/src/components/ui/StatusBadge.tsx)**: Standardizes scan status representation.
- **[StatsCard.tsx](file:///mnt/d/Projects/MedAI-3D-CT-Scan-System/frontend/src/components/ui/StatsCard.tsx)**: Standardizes dashboard statistics.
- **[EmptyState.tsx](file:///mnt/d/Projects/MedAI-3D-CT-Scan-System/frontend/src/components/ui/EmptyState.tsx)**: Standardizes placeholder states for empty tables or lists.
- **[LoadingSkeleton.tsx](file:///mnt/d/Projects/MedAI-3D-CT-Scan-System/frontend/src/components/ui/LoadingSkeleton.tsx)**: Provides skeleton screens for dashboards, tables, and cards during data fetching.
