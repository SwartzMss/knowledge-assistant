# Runtime flows

## Startup and UI construction

```mermaid
sequenceDiagram
    participant Entry as app.py
    participant Settings as flowsettings
    participant App as ktem.main.App
    participant IndexMgr as IndexManager
    participant DB as SQLite
    participant UI as Gradio

    Entry->>Settings: import resolved settings
    Settings->>Settings: create local directories and provider specs
    Entry->>App: App()
    App->>App: register Pluggy extensions and reasonings
    App->>IndexMgr: initialize and load indices
    IndexMgr->>DB: create/read index records
    IndexMgr->>IndexMgr: construct and start FileIndex objects
    Entry->>App: make()
    App->>UI: render pages, states, and callbacks
    Entry->>UI: queue().launch()
```

Important behavior:

- Import and initialization are not side-effect free.
- Indices are available before UI construction because their settings and pages affect the rendered component tree.
- Public events are an in-process callback mechanism, not an external event bus.
- Gradio session state carries flattened settings and the current user identifier.

## File ingestion

The ingestion path starts in a large Gradio page callback and ends in multiple stores.

```mermaid
sequenceDiagram
    participant User
    participant UI as FileIndexPage
    participant Pipeline as IndexDocumentPipeline
    participant Reader as PDF/TXT/MD reader
    participant Splitter as TokenSplitter
    participant Embed as Embedding model
    participant SQL as SQLite
    participant DS as LanceDB
    participant VS as ChromaDB
    participant FS as Local files

    User->>UI: upload file(s)
    UI->>UI: extension/size/count validation
    UI->>Pipeline: stream(file paths)
    Pipeline->>Reader: parse selected file
    Reader-->>Pipeline: Document list
    Pipeline->>Splitter: chunk documents
    Splitter-->>Pipeline: chunks
    Pipeline->>Embed: embed chunks
    Pipeline->>DS: persist chunk documents
    Pipeline->>VS: persist vectors and metadata
    Pipeline->>FS: copy original file
    Pipeline->>SQL: write source and source-to-chunk relations
    Pipeline-->>UI: progress/debug documents and result
```

The exact write order lives in `ktem/index/file/pipelines.py`. Because these writes are not one transaction, interruption can leave partial state. Delete/rebuild functions are therefore operationally important, but today there is no durable job record, idempotency key, or reconciliation worker.

### Ingestion invariants to formalize

- A source record must refer to an existing original file.
- Every source-to-chunk relation must refer to a document-store entry.
- Every vector entry must have a retrievable document chunk with compatible embedding dimensions.
- Reindexing the same file must have explicit replace/version semantics.
- Failure at any stage must be retryable or compensatable.
- The model and splitter configuration used to build an index must be recorded.

## Retrieval

`FileIndex.get_retriever_pipelines()` resolves the configured retriever class and supplies index resources, user settings, and selected source IDs. The default `DocumentRetrievalPipeline` can combine vector and text retrieval and optionally generate relevance scores.

```mermaid
flowchart LR
    Query["User query"] --> Resolve["Resolve selected files/groups"]
    Resolve --> Filter["Build user/source filters"]
    Filter --> Vector["Vector retrieval"]
    Filter --> Text["Document-store text retrieval"]
    Vector --> Merge["Merge/deduplicate/rank"]
    Text --> Merge
    Merge --> Docs["RetrievedDocument list"]
```

Private indices scope sources by user. This authorization rule is embedded in index and retrieval logic; it should become an explicit policy test before any API is exposed.

## Chat and answer generation

```mermaid
sequenceDiagram
    participant User
    participant Chat as ChatPage
    participant Reason as FullQAPipeline
    participant Ret as Retriever(s)
    participant Evidence as PrepareEvidencePipeline
    participant LLM as Chat model
    participant Citation as Citation pipeline
    participant DB as Conversation store

    User->>Chat: submit message
    Chat->>Chat: resolve settings, conversation, selected data
    Chat->>Reason: create pipeline and stream(...)
    Reason->>Ret: retrieve query context
    Ret-->>Reason: retrieved documents/plots
    Reason-->>Chat: stream evidence-panel updates
    Reason->>Evidence: format bounded context/images
    Reason->>LLM: stream answer with history and evidence
    LLM-->>Reason: answer tokens
    Reason-->>Chat: stream chat tokens
    Reason->>Citation: match answer to evidence
    Reason-->>Chat: citations, confidence, plots
    Chat->>DB: persist conversation data_source/history
```

Relevance scoring may run in a thread while the answer is generated; the reasoning pipeline joins that thread before presenting final evidence. There is an asynchronous method placeholder, but the active path is synchronous generator streaming.

## Error and observability behavior

Current behavior relies mainly on exceptions, console output, and streamed `Document(channel="debug"|"info")` messages. There is no consistent correlation ID across upload, retrieval, model request, and conversation. A minimum observability layer should add:

- request, conversation, user, index, source, and ingestion-job identifiers;
- structured logs with secret/content redaction;
- stage timings and document/chunk counts;
- provider latency/error/token metrics;
- health checks for SQLite, document store, vector store, and configured providers;
- a user-safe error taxonomy distinct from developer diagnostics.
