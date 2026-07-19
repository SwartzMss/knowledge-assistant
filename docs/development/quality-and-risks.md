# Quality and risk assessment

## Summary

The codebase has solid reusable primitives and a reproducible lockfile, but the application is not production-ready. The largest risks are boundary and lifecycle risks rather than the basic RAG algorithm: secrets/authentication defaults, multi-store consistency, UI-to-domain coupling, unversioned schemas, and an oversized inherited dependency/capability surface.

Priority definitions:

- **P0**: address before any production or externally reachable deployment.
- **P1**: address before significant feature work or API exposure.
- **P2**: improve during modularization and scale preparation.

## Risk register

| Priority | Finding | Evidence in current code | Consequence | Recommended control |
| --- | --- | --- | --- | --- |
| P0 | Default admin credentials | `flowsettings.py` defaults admin username/password to `admin` | Immediate account takeover if exposed | Require first-run secret/bootstrap; reject defaults outside dev |
| P0 | Gradio share/external exposure lacks a hardened deployment boundary | `KH_GRADIO_SHARE`; direct Gradio launch | Accidental public access, weak rate/audit controls | Default local-only; deploy behind authenticated reverse proxy/API |
| P0 | Multi-store writes are non-transactional | Index pipeline writes SQLite, FS, LanceDB, Chroma | Orphans and inconsistent retrieval after failures | Durable ingestion jobs, idempotency, compensation/reconciliation |
| P0 | No supported migration path | `create_all` at import; Alembic disabled | Unsafe upgrades and irreversible schema drift | Enable/version migrations and test upgrades/restores |
| P1 | UI owns application orchestration | Chat/file pages construct pipelines and query persistence | Hard to test, reuse, expose as API, or enforce policies | Introduce application services/use cases |
| P1 | Authorization rules are distributed | User/private filtering lives in UI/index/retriever paths | Cross-user data exposure when adding new entry points | Central policy layer plus negative authorization tests |
| P1 | Provider/config errors are late and dynamic | Dotted imports and `__type__` dictionaries | Runtime failures after startup/user action | Typed config validation and startup capability checks |
| P1 | Broad dependency surface | Core package installs many providers/loaders/frameworks | Slow builds, vulnerability surface, version conflicts | Split baseline and extras; remove unsupported runtime deps |
| P1 | Weak application E2E coverage | CI covers compile/import, core unit tests, minimal ktem tests | Regressions in upload-chat-citation path | Deterministic fake-provider integration and browser smoke tests |
| P1 | No structured observability | Prints and streamed debug documents | Incidents cannot be correlated or measured | Structured logs, metrics, tracing IDs, health/readiness |
| P2 | Dynamic per-index SQL tables | `FileIndex._setup_resources()` | Migration and operations complexity | Stable normalized schema with `index_id` |
| P2 | Large UI module | file UI exceeds 1,500 lines; chat page mixes state/data/render | High change risk and ownership ambiguity | Split controllers/presenters from services and view components |
| P2 | Sync/thread hybrid execution | synchronous generators plus relevance thread | Cancellation/resource-leak complexity | Define job/execution model; bound pools and cancellation |
| P2 | Retained unsupported code lacks classification | agents/OCR/web/MCP/alternative stores remain | Misleading support claims and maintenance load | Capability inventory and explicit lifecycle labels |

## Test assessment

Current strengths:

- Kotaemon has unit tests across documents, loaders, models, stores, retrieval, reranking, agents, and telemetry.
- Ktem has minimal login, conversation, baseline, and QA-oriented tests.
- CI builds docs strictly, compiles the application, verifies imports/package metadata, runs upstream core tests on Python 3.10/3.11, and runs the minimal app suite.
- `uv.lock` and frozen sync improve reproducibility.

Gaps to close:

1. A no-network integration test that uploads a fixture, indexes it with a deterministic fake embedding, retrieves it, answers with a fake streaming LLM, and verifies citations.
2. Failure-injection tests after each persistence stage, followed by retry/reconciliation.
3. Authorization tests for private/public indices, conversations, groups, downloads, and deletion.
4. Migration tests from at least the previous released data/schema version.
5. Browser smoke tests for login, upload, chat, citation navigation, settings, and logout.
6. Load tests for parallel chat, large uploads, cancellation, and provider timeouts.
7. Contract tests for each supported model/store adapter.

Recommended test pyramid:

| Layer | Purpose | CI target |
| --- | --- | --- |
| Unit | Components, policies, config, transformations | Every push, fast |
| Contract | Store/provider adapter behavior | Every PR for baseline adapters |
| Integration | Application services with local real stores/fake models | Every PR |
| Browser E2E | Critical user journeys | Every PR or merge queue |
| Migration/restore | Upgrade and backup safety | Every release |
| Load/resilience | Capacity and failure behavior | Scheduled/pre-release |

## Security baseline

Before production, implement:

- password hashing verification, bootstrap/admin rotation, session expiration, CSRF and secure-cookie review;
- upload MIME/content validation, archive limits, path normalization, malware scanning hook, and parser sandbox strategy;
- per-user/index authorization enforced below the UI layer;
- model endpoint allowlists or SSRF protections for configurable endpoints;
- secrets through environment/secret manager only, with log redaction;
- rate, upload-size, token-budget, and concurrency limits;
- dependency and container scanning plus a vulnerability response process;
- audit records for login, source access, upload, delete, settings changes, and admin actions;
- documented data retention and deletion behavior, including vector/document replicas.

## Performance and scalability

The single-process design is adequate for development and small local installations. Expected pressure points are CPU-heavy parsing, embedding/network concurrency, SQLite write contention, Gradio worker occupancy during long streams, and memory/context growth.

Measure before splitting services. Establish metrics for upload bytes, parse/chunk/embed time, chunks per source, retrieval latency/recall proxy, time-to-first-token, total answer latency, token usage, error/retry rate, queue depth, and store sizes. Move ingestion to a worker first when durable background execution is required; move query serving only when independent scaling or isolation is demonstrated.
