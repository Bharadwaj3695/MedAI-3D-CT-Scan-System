# ADR-001: Selection of FastAPI for Backend Framework

* **Date**: June 30, 2026
* **Status**: Approved

## Context
We need a backend framework to orchestrate file uploads, coordinate database transactions, and serve as an API gateway for our deep learning model. The model is written in Python (PyTorch), which requires a Python-compatible backend to avoid inter-process communication overhead.

We considered:
1. **Flask**: Minimalist and flexible, but lacks built-in asynchronous support and automatic OpenAPI documentation.
2. **Django**: Full-featured, but heavy and historically synchronous-first, making it harder to integrate with async file streaming.
3. **FastAPI**: Modern, fast (ASGI-based), type-safe, and natively supports asynchronous operations.

## Decision
We chose **FastAPI** as the primary backend framework.

## Consequences
* **Positives**:
  - Out-of-the-box OpenAPI/Swagger documentation, saving development time.
  - Native support for Pydantic schemas, ensuring strict request/response validation.
  - Excellent performance via ASGI (Uvicorn), allowing asynchronous file reads.
  - Easily offloads blocking CPU-bound tasks (like model inference) to an external threadpool by using standard synchronous `def` route handlers.
* **Negatives**:
  - Smaller ecosystem compared to Django, requiring us to manage database migrations and authentication integrations manually.
