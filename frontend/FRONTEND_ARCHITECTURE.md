# ScholarGraph AI — Frontend Architecture

## Overview
This document outlines the frontend architecture for the ScholarGraph AI / ResearchPaperAnalyzer project. The architecture is designed to be highly modular, component-driven, and seamlessly integrate with the robust backend APIs.

## Stack
- **Framework**: React 19 + Vite
- **Routing**: React Router v7
- **Styling**: Tailwind CSS v4
- **Icons**: Lucide React
- **Visualization**: react-force-graph-2d

## Folder Structure
```text
frontend/
├── src/
│   ├── api/                  # Centralized API client and route definitions
│   │   ├── client.js         # Fetch wrapper with error handling and environment injection
│   │   ├── exports.js        # Export links mapping
│   │   ├── literature.js     # Literature analysis endpoints
│   │   ├── papers.js         # Paper upload and retrieval endpoints
│   │   └── index.js          # Unified API exports
│   │
│   ├── components/           # Reusable UI components
│   │   ├── common/           # Generic buttons, badges, loaders, error states
│   │   ├── layout/           # Global structure: AppShell, Topbar, Sidebar, PageContainer
│   │   └── ...               # Domain-specific components (UploadPaper, PaperList, etc.)
│   │
│   ├── pages/                # Route-level views (Dashboard, Papers, UploadPaper, PaperDetail, NotFound)
│   │
│   ├── App.jsx               # Route definitions and Router instantiation
│   └── main.jsx              # Application entrypoint
│
├── .env                      # Environment configuration
└── package.json              # Dependencies and scripts
```

## API Architecture
The frontend utilizes a custom lightweight HTTP client (`src/api/client.js`) wrapping the native `fetch` API. 
Key responsibilities:
- **Environment Targeting**: Utilizes `VITE_API_BASE_URL` rather than hardcoding paths.
- **Error Normalization**: Maps backend validation and process exceptions (`{"error": {"code": "...", "message": "..."}}`) directly to frontend `ApiError` objects, avoiding trace leaks or raw HTTP dumps in the UI.
- **Headers & Serialization**: Automatically formats JSON payloads or skips parsing empty `204` responses.

## Routing
Routing is built with React Router v7 inside an `AppShell` container.
Current valid routes:
- `/` - Dashboard (Research Intelligence Overview)
- `/papers` - Library of uploaded research
- `/upload` - Paper PDF Upload gateway
- `/papers/:id/research` - Research Workspace entrypoint
- `/papers/:id/research/overview` - Paper Abstract & High-Level Stats
- `/papers/:id/research/profile` - Extracted Research Domain & Methodology
- `/papers/:id/research/related` - Literature Discovery Results
- `/papers/:id/research/analysis` - Granular Paper Comparisons & Findings
- `/papers/:id/research/survey` - Synthesized Literature Review
- `/papers/:id/research/gaps` - Identified Research Opportunities
- `/papers/:id/research/recent` - Emerging Research Timeline
- `/papers/:id/research/graph` - Citation & Semantic Landscape Graph
- `/papers/:id/research/compare` - Advanced Multi-Paper Literature Comparison
- `/papers/:id/research/intelligence` - Consolidated Research Gap & Opportunity Intelligence

## Research Workspace Architecture
The Research Workspace serves as the primary analysis interface, loading a target paper and managing navigation across sub-domain tabs.

- **Component Structure**: `ResearchWorkspace.jsx` wraps `ResearchHeader.jsx` and `ResearchTabs.jsx`. It utilizes a shared `Outlet` context to pass down `paper` and `pipelineStatus` to sub-components.
- **Loading Strategy**: Each tab operates independently. The parent Workspace fetches the root paper metadata and processing status. Individual tabs (`ResearchProfile`, `LiteratureAnalysis`, etc.) fetch their own data directly through `literatureApi`. This ensures the UI remains highly responsive and does not block on heavily delayed or processing background tasks.
- **Error Isolation**: Error boundaries and empty states are confined to individual tabs. If the literature survey fails to generate, the user can still access related papers or the research profile without the entire workspace collapsing.
- **Export Behavior**: The `ResearchHeader` features a unified export dropdown providing direct downloads to JSON, Markdown, and PDF assets served directly from the backend endpoints.
- **Graph Integration**: The existing `CitationGraph.jsx` is securely wrapped inside `ResearchGraph.jsx` and now fetches data using the centralized `client.js`.

## Paper Comparison Architecture
The Paper Comparison feature (`PaperComparison.jsx`) allows researchers to compare the target paper side-by-side against up to 3 selected related papers.

- **Selection Flow**: Users can select papers for comparison via checkboxes in `RelatedPapers.jsx`, a `[Compare With Target]` button inside the `ResearchGraph.jsx` node details, or through the inline dropdown inside the `PaperComparison` screen.
- **Comparison Data Mapping**: Target Paper metadata is synthesized from its core entity combined with the `ResearchProfile`, whereas related papers populate their columns using data directly from the `LiteratureAnalysis` endpoint. Structural fields (like "Methodology" or "Key Findings") map directly to table rows.
- **URL State**: The selected paper identifiers are injected into the URL as query parameters (`?papers=...`), enabling bookmarking, sharing, and browser back/forward capabilities without needing global state management.
- **Partial Analysis Handling**: If an analysis payload is partially incomplete or currently generating, the frontend gracefully isolates the UI (displaying "Analysis unavailable" place-holders for missing elements) without blowing up the larger DOM payload.
- **Responsive & Accessibility Strategy**: The comparison layout utilizes a semantic `<table />` encapsulated inside an `overflow-x-auto` utility block. Each paper represents a column, maintaining horizontal integrity even on mobile devices.
- **Performance Strategy**: Analysis and profile requests are batched using `Promise.allSettled()`. Paper data parsing is memoized natively by React hooks, shielding excessive component renders when manipulating localized DOM state.

## Research Intelligence Architecture
The Research Intelligence feature (`ResearchIntelligence.jsx`) aggregates findings from the Gap Detection and Recent Research services to identify actionable Research Opportunities.

- **Data Composition**: Merges the responses of `/papers/:id/literature/gaps` and `/papers/:id/literature/recent`. Uses `Promise.allSettled()` to fetch both endpoints concurrently. A failure in one gracefully degrades rather than failing the whole page.
- **URL State Tabs**: Navigation between Opportunities, Gaps, and Recent Developments is persisted in the URL query string (`?tab=...`), enabling direct links to specific intelligence views.
- **Opportunities Mapping**: Dynamically links identified Research Gaps to recent papers that explicitly flag `addresses_gap=True`. Does not invent connections or hallucinate semantic similarities.
- **Gap UI**: Interactive Gap Cards with visual confidence bars, proposed directions, and evidence lists. Clicking a gap triggers a semantic Details Drawer overlay.
- **Recent UI**: Chronological timeline rendering of recent papers with sort/filter controls. Highlights `Addresses Research Gap` badges where provided by the backend. Includes deep-links to the Paper Comparison route for detailed evaluation.
- **Safe Intelligence Guidelines**: The UI enforces strict neutral language. It displays "Proposed Direction" instead of "You must do this", and avoids creating fake metrics if backend arrays are empty.

## Dashboard & Library Architecture
The Global Dashboard and Research Library handle multi-paper navigation, aggregation, and bulk operations safely across the user's workspace without invoking severe N+1 request cascades.

- **Dashboard Metrics**: Dashboard statistics (Total, Processed, Processing, Failed) are safely derived from a single `/papers` fetch limit slice. Analytics hallucination is strictly prevented.
- **Local Filtering System**: Because the backend limits arbitrary property queries, `PaperList.jsx` utilizes localized useMemo-driven filtering across the maximum backend pagination depth. 
- **URL State Persistance**: Global search strings, sort parameters (`sort=newest`), status toggles (`status=COMPLETED`), and local page indexes are persistently synced with React Router's `useSearchParams`.
- **Global Search**: The topbar exposes a site-wide semantic search input that seamlessly routes payloads to `/papers?search=...` for centralized evaluation.
- **Safe Deletion**: Deleting research papers triggers a confirmation flow, followed by an atomic frontend state-invalidation and re-fetch to maintain alignment with backend cascades.

## Frontend Production Readiness
This section documents the state of the frontend following Phase 8.

- **Testing**: Exhaustive manual and regression tests performed against all primary workflows.
- **Accessibility**: Audited for semantic HTML, focus management, ARIA roles, high contrast boundaries, and keyboard navigation completeness.
- **Security**: Zero API secrets in source. Markdown payload injection fully mitigated via React native sanitization escapes. 
- **Performance**: Confirmed mitigation of N+1 cascading API queries. Skeletons deployed correctly.
- **Export Verification**: File download streams decoupled correctly into blob URL generators.
- **API Contract Verification**: No mock data remains in production flows. Frontend assumes nothing about optional keys in backend response objects.
- **Production Build**: Vite builds pass with 0 errors and output well-optimized chunks.
- **Known Limitations**: The PaperList relies on localized filtering which restricts scale to ~100 parallel items; any more requires backend query indexing.
