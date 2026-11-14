# Inventory & Sales RAG Practice — Groq + Jina + FAISS

Practice build following the free-tier stack: **Groq** (LLM, free tier),
**Jina** (embeddings, free tier), **FAISS** (local vector store, free).
Same workflow as the reference video — rebuilt on Inventory & Sales
policy data instead of HR, so this is genuinely yours to teach from.

Two ways to use it:

- **Web app** — `streamlit run streamlit_app.py` (simple chat UI,
  streamed answers; built on the `rag/` package)
- **Terminal** — `python rag_sales.py` (the original single-file
  pipeline, kept exactly as it was: stage-by-stage report, smoke
  tests, interactive REPL)

## Project structure

```
DevRecruit_RAG_1/
├── rag/                    # the pipeline, one module per stage
│   ├── config.py           # settings, paths, API-key checks
│   ├── ingest.py           # stage 1-2: load documents, chunk them
│   ├── embeddings.py       # stage 3: Jina-backed Embeddings (REST API)
│   ├── vectorstore.py      # stage 4: FAISS index
│   ├── llm.py              # stage 5: Groq chat model
│   ├── tools.py            # stage 6: the search_policy tool
│   ├── agent.py            # stage 7: create_agent + system prompt
│   └── pipeline.py         # assembly + ask/stream helpers
├── rag_sales.py            # the original all-in-one pipeline (kept for teaching)
├── streamlit_app.py        # Streamlit chat frontend
├── rag_stage_breakdown.pdf # printable handout of the mapping table below
├── .streamlit/config.toml  # theme (colors, font)
├── data/policies.txt       # the policy documents
├── requirements.txt
└── .env                    # your API keys (not tracked by git)
```

### How the breakdown maps

Each `# STAGE` block in `rag_sales.py` became exactly one file in `rag/`:

| In `rag_sales.py` (the "before") | In `rag/` (the "after") | What moved |
|---|---|---|
| Top imports + key checks | `rag/config.py` | Settings, paths, `require_key()` — one place to look up config |
| `# STAGE 1: DATA INGESTION` + `# STAGE 2: CHUNCKING` | `rag/ingest.py` | `load_documents()`, `chunk_documents()` |
| `# Embedding(JINA API)` + the `JinaEmbeddings` class | `rag/embeddings.py` | The ~30-line REST-call embeddings class |
| `# STAGE 4: vector store` | `rag/vectorstore.py` | `build_vector_store()` — FAISS indexing |
| `# STAGE 5 - THE LLM(Groq)` | `rag/llm.py` | `build_llm()` — ChatGroq |
| `# STAGE 6 — THE TOOL` | `rag/tools.py` | `search_policy` — the docstring doubles as the tool description |
| `# STAGE 7 — THE AGENT` | `rag/agent.py` | `SYSTEM_PROMPT` + `create_agent` |
| `# HELPERS` + assembly glue | `rag/pipeline.py` | `build_pipeline()` ties the stages together; `ask_assistant()` / `stream_answer()` are what entry points call |
| `# ENTRY POINT` / `chat_loop` | stays in `rag_sales.py` | Entry points stay thin — now there are two: the CLI and `streamlit_app.py` |

A printable one-page version of this table is in `rag_stage_breakdown.pdf`.

## What's been verified already
- ✅ Project scaffolded, dependencies installed (`requirements.txt` pinned)
- ✅ `.env` / `.gitignore` wired correctly — secrets never get tracked by git
- ✅ Data loading + chunking confirmed working (13 clean chunks from
  `data/policies.txt` — one chunk per policy)
- ✅ **Jina embeddings** verified live: `jina-embeddings-v5-text-small` turns the
  chunks into vectors over the real API (no Hugging Face, no local model download,
  no PyTorch)
- ✅ FAISS index built from those Jina vectors, similarity search returns the
  right return-policy chunk
- ✅ Groq agent verified end-to-end — all three sample questions answered from
  `data/policies.txt` via the `search_policy` tool

## What you need to do on your own machine

### 1. Get free API keys
- **Groq**: console.groq.com → sign in → API Keys → Create API Key
- **Jina**: jina.ai → sign in → get API key (generous free tier)

### 2. Fill in `.env`
Replace the placeholders in `.env` with your real keys:
```
GROQ_API_KEY=gsk_your_real_key
JINA_API_KEY=jina_your_real_key
```

### 3. Run it

Web app (recommended):
```bash
streamlit run streamlit_app.py
```

Terminal:
```bash
python rag_sales.py
```

In the terminal you'll see: environment loaded → document loaded →
13 chunks → Jina embeddings ready → FAISS indexed with Jina vectors →
a raw similarity search result → the LLM ready → three sample questions
asked and answered by the agent, using the `search_policy` tool to ground
its answers in `data/policies.txt`.

In the web app the same pipeline builds once (cached in the server
process), then you just chat: answers stream in with a small
"searched the policies" indicator while the agent works, and editing
`data/policies.txt` re-indexes automatically on the next message.

## Try asking it yourself
- "Can I return an opened electronics item after 10 days?"
- "How is the reorder quantity calculated?"
- "What happens if a supplier pays late?"
- "My laptop stopped working after 8 months — is it still covered?"
- "Do you match a cheaper price I saw at another store?"
- "A box arrived with two items missing. What do I do?"
- "How long is a gift card valid, and can I get cash for it?"

## What to notice while you run this (teaching points)
- **Jina embeddings are just an HTTP call.** `rag/embeddings.py` is ~30 lines:
  POST text to `https://api.jina.ai/v1/embeddings`, get vectors back. No local
  model, no GPU, no `sentence-transformers`. That demystifies "embedding model"
  for trainees — it's an API, same as the LLM.
- **Retrieval is asymmetric.** Jina gives documents the `retrieval.passage`
  adapter and questions the `retrieval.query` adapter. LangChain's `Embeddings`
  interface already splits these into `embed_documents()` and `embed_query()`,
  which is exactly why those are two methods instead of one. Swap the tasks
  around and show retrieval quality drop — great live demo.
- **The system prompt explicitly forbids** the assistant from promising a
  refund directly — this is the safety-guardrail pattern from Phase 2,
  now doing real work in an agent's instructions, not just a lecture point.
  (`rag/agent.py`)
- `create_agent` is LangChain's newer, higher-level way to build an agent —
  compare this to the raw `tools_schema` + manual loop from the Build
  Guide's Phase 5. Teach the raw version first so trainees understand
  what `create_agent` is doing for them underneath.
- **Same pipeline, two shapes.** `rag_sales.py` is the original
  all-in-one file — every stage inline, marked with `# STAGE ...`
  comments. The `rag/` package is that exact pipeline broken into one
  file per stage, and `streamlit_app.py` (the web UI) builds on the
  package. Walk students through the single file first, then show how
  each `# STAGE` comment became a file in the folder.
- **Grounding is inspectable.** `rag/tools.py` records every retrieval into
  `pipeline.last_sources`, so the exact chunks behind an answer are always
  available in code — a concrete way to discuss hallucination and grounding
  in class. The web UI keeps the chat minimal; add a small "sources"
  expander in `streamlit_app.py` if you ever want it visible.
- `langchain-community` is flagged as being sunset in favor of standalone
  integration packages. Jina's third-party `langchain-jina` package currently
  pins old `langchain-core` versions, which is why `rag/embeddings.py` talks
  to the Jina REST API directly instead of depending on it. Worth mentioning
  to trainees that the ecosystem moves fast — checking a package's current
  compatibility is a real, ongoing AI-engineering skill, not a one-time lesson.

## Where this plugs into the Django app
This exact pattern — `TextLoader` → `RecursiveCharacterTextSplitter` →
embeddings → `FAISS`/Chroma → `create_agent` with a `search_policy` tool —
is the LangChain-framework version of what the Build Guide's Step 8-9
built with raw OpenAI calls and Chroma. Once you're comfortable with both,
decide which one to actually teach: raw code teaches the concepts more
transparently; `create_agent` ships faster. Many instructors teach raw
first, then show this as "the shortcut, now that you know what's really
happening."
# SalesBot_Assign
