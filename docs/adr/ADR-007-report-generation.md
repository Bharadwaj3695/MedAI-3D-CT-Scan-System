# ADR-007: Selection of HTML Templates for Report Generation

* **Date**: June 30, 2026
* **Status**: Approved

## Context
After a scan is analyzed, the system must generate a structured report containing findings, recommendations, and patient metadata. This report needs to be downloadable and printable.

We considered:
1. **PDF Generation (ReportLab / WeasyPrint)**: Direct PDF compilation, but highly rigid and difficult to style dynamically.
2. **HTML Templates**: Rendered using Jinja2 and styled with CSS. Can be displayed directly in the browser and printed to PDF using native browser print dialogs.

## Decision
We chose **HTML Templates** (using Jinja2 on the backend) for report generation.

## Consequences
* **Positives**:
  - Flexibly styled using modern CSS.
  - Can be rendered directly in the frontend inside an iframe or modal, providing a seamless user experience.
  - Leverages native browser engines (`window.print()`) to generate high-quality PDFs without server-side rendering overhead.
* **Negatives**:
  - PDF layout consistency relies on the user's browser print engine, which can vary slightly between Chrome, Firefox, and Safari.
