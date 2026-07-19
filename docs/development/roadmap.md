# Implementation roadmap

## Recommended sequence

The roadmap is ordered to reduce risk while keeping the current product usable. Time ranges are rough engineering estimates for one experienced developer and should be recalibrated after the first milestone.

## Phase 0 — baseline and safety (2–4 days)

Deliverables:

- Record the supported product matrix: file types, stores, providers, OS/Python versions.
- Add a deterministic upload → index → retrieve → stream answer → citation integration test.
- Add negative authorization tests for private knowledge bases and conversations.
- Reject default admin credentials outside explicit development mode.
- Document/guard local-only binding and Gradio share mode.
- Capture a fixture copy of the current data schema for future migration tests.

Exit criteria:

- Critical RAG behavior can be verified without external network calls.
- A breaking refactor fails CI at the application boundary.
- Known production-blocking defaults cannot silently ship.

## Phase 1 — typed bootstrap and application services (1–2 weeks)

Deliverables:

- Introduce a typed `AppConfig` that resolves environment and defaults once.
- Separate directory creation/provider construction from configuration parsing.
- Add startup validation for model, embedding, store, and index compatibility.
- Create thin `KnowledgeBaseService`, `IngestionService`, `QueryService`, and `ConversationService` wrappers over existing implementations.
- Move authorization checks into service/policy methods.
- Make Gradio callbacks call services rather than SQL/pipelines directly.
- Add structured domain errors and user-safe error mapping.

Exit criteria:

- Application use cases run in tests without constructing Gradio UI.
- UI modules contain rendering/event adaptation, not storage queries or provider construction.
- Invalid configuration fails at startup with actionable messages.

## Phase 2 — persistence lifecycle and recovery (1–2 weeks)

Deliverables:

- Enable Alembic and create an initial stamped schema.
- Replace new dynamic per-index tables with normalized tables using `index_id`; provide compatibility/migration code for existing data.
- Add index manifests with embedding dimension/model and chunking configuration.
- Implement durable ingestion job states, deterministic chunk/vector IDs, retries, and cancellation.
- Add reconciliation, export, backup, restore, and integrity-check commands.
- Add failure-injection and upgrade/restore tests.

Exit criteria:

- Killing ingestion at any stage yields a retryable or automatically repairable state.
- Upgrade and restore from the previous supported schema are automated and tested.
- Delete semantics cover every physical copy and produce an audit record.

## Phase 3 — observability and operational readiness (3–5 days)

Deliverables:

- Structured logging with request/conversation/job/source identifiers.
- Metrics for ingestion stages, retrieval, model calls, queues, tokens, and errors.
- Liveness/readiness and dependency health endpoints or commands.
- Timeout, retry, concurrency, upload, and token-budget policies.
- Operator runbooks for provider failure, corrupt index, full disk, backup/restore, and credential rotation.

Exit criteria:

- An operator can identify a failed request/job and its stage without reproducing it.
- Health signals distinguish process health from dependency readiness.

## Phase 4 — dependency and capability cleanup (3–7 days)

Deliverables:

- Classify retained modules as supported/experimental/compatibility/remove.
- Move optional providers, OCR, agents, web search, alternate stores, and MCP dependencies into extras.
- Remove Gradio/FastAPI dependencies from core packages where not intrinsically required.
- Add adapter contract tests for every supported provider/store.
- Publish a compatibility matrix and deprecation policy.

Exit criteria:

- A minimal installation contains only baseline runtime dependencies.
- Supported capability claims match registered configuration and CI coverage.

## Phase 5 — external interfaces (optional, 1–2 weeks)

Prerequisite: phases 0–3 complete.

Deliverables:

- Versioned HTTP API over application services with authentication and quotas.
- MCP adapter over the same query/source contracts if required.
- OpenAPI/schema documentation, streaming protocol, error model, idempotency rules.
- API contract, authorization, rate-limit, and client compatibility tests.

Exit criteria:

- Gradio and external clients produce equivalent policy and domain behavior.
- No transport bypasses authorization, auditing, budgets, or application services.

## Phase 6 — worker/service split (only with measured need)

Start with ingestion workers. Define SLOs and capacity evidence before splitting query services. Required design items include job ownership, idempotency, outbox/event delivery, distributed tracing, deployment rollback, and data/schema compatibility.

## First backlog

| Order | Work item | Acceptance test |
| --- | --- | --- |
| 1 | Deterministic full RAG integration fixture | One test validates upload, retrieval, streaming answer, citation |
| 2 | Secure bootstrap credentials | Non-dev startup refuses `admin/admin` |
| 3 | Typed effective configuration | One validated object; secrets excluded from repr/logs |
| 4 | `IngestionService` wrapper | UI callback delegates and service is Gradio-free |
| 5 | `QueryService`/`ConversationService` | Chat path tested without rendering UI |
| 6 | Central authorization policy | Cross-user reads/downloads/deletes fail in service tests |
| 7 | Alembic baseline | Empty and existing fixture DBs reach current revision |
| 8 | Ingestion job table/state machine | Interrupted job can retry without duplicate chunks |
| 9 | Integrity/reconciliation CLI | Detects and reports injected orphan in each store |
| 10 | Structured telemetry | One correlation ID links request, retrieval, provider call, response |

## Definition of done for architecture work

An architecture change is complete only when code, migration/compatibility handling, automated tests, operational behavior, and developer documentation land together. Diagrams must describe the implemented state; proposals remain explicitly labeled TO-BE until their acceptance criteria pass.
