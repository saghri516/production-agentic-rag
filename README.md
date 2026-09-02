<p align="center">
  <img alt="Agentic RAG Logo" src="assets/logo.png" width="350px">
</p>

<h1 align="center">Production Agentic RAG</h1>

<p align="center">
  <strong>A multi-agent RAG system built on LangGraph — hardened from a learning prototype into a deployable, persistent, secured application.</strong>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#engineering-highlights">Engineering Highlights</a> •
  <a href="#setup">Setup</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#known-limitations">Known Limitations</a> •
  <a href="#troubleshooting">Troubleshooting</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/LangGraph-1.2%2B-orange?logo=langchain&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Qdrant-vector%20db-DC244C" alt="Qdrant"/>
  <img src="https://img.shields.io/badge/PostgreSQL-checkpointer-336791?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/LLM-Groq-f55036" alt="Groq"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

## Overview

This project answers natural-language questions over a set of indexed PDF documents using a **coordinator-and-subagent LangGraph architecture**: a top-level agent plans and rewrites the query, delegates chunk retrieval and analysis to specialist subagents running in parallel, compresses context to stay within budget, and synthesizes a single source-cited answer.

It was engineered to run as a real, deployable service rather than a local script — adding persistent state, authentication, rate limiting, resilience against LLM provider failures, and a Docker-based deployment, all verified through hands-on testing.

### Core RAG Features

| Feature | Description |
|---|---|
| 🗂️ **Hierarchical Indexing** | Search small child chunks for precision, retrieve large parent chunks for context |
| 🧠 **Conversation Memory** | Rolling summary + recent history, persisted per session |
| ❓ **Query Clarification** | Human-in-the-loop interrupt when a question is ambiguous |
| 🤖 **Agent Orchestration** | LangGraph coordinates retrieval, reasoning, and synthesis |
| 🔀 **Multi-Agent Map-Reduce** | Parallel subagents per decomposed sub-question |
| ✅ **Self-Correction** | Re-queries automatically when initial retrieval is insufficient |
| 🗜️ **Context Compression** | Keeps working memory lean across long retrieval loops |

### Production Hardening

| Feature | Description |
|---|---|
| 🐘 **Postgres Persistence** | Conversation state survives restarts via `PostgresSaver`, replacing in-memory checkpointers |
| 🔁 **Retry & Fallback** | `tenacity`-based exponential backoff around every LLM call, with graceful degradation instead of crashes |
| 🔐 **Authentication** | Gradio-level username/password auth, failing loud if credentials aren't configured |
| 🚦 **Rate Limiting** | Per-session sliding-window limiter, blocking abuse before it reaches the LLM |
| 🧵 **Session Isolation** | Per-browser-session `thread_id` via `gr.State()` — prevents cross-user conversation bleed |
| 📋 **Structured Logging** | Consistent, leveled logging in place of scattered `print()` calls |
| 🐳 **Docker Deployment** | `docker-compose.yml` running app + Postgres + Qdrant as health-checked services |
| 🧪 **Unit Tests** | Full test coverage for document processing and table-of-contents filtering logic |

## Architecture

```mermaid
flowchart TD
    U[User] -->|question| GR[Gradio UI<br/>per-session thread_id]
    GR -->|authenticated request| RL{Rate Limiter}
    RL -->|blocked| U
    RL -->|allowed| SH[Summarize History]
    SH --> RW[Rewrite Query]
    RW -->|ambiguous| CL[Request Clarification]
    CL -.->|interrupt, wait for user| RW
    RW -->|clear| AG[Agent Subgraph]

    subgraph AG[Agent Subgraph]
        direction TB
        ORCH[Orchestrator] -->|tool call| TOOLS[search_child_chunks /<br/>retrieve_parent_chunks]
        TOOLS --> COMPRESS{Context too large?}
        COMPRESS -->|yes| COMPACT[Compress Context]
        COMPACT --> ORCH
        COMPRESS -->|no| ORCH
        ORCH -->|answer ready| COLLECT[Collect Answer]
        ORCH -->|LLM failure, retries exhausted| FALLBACK[Fallback Response]
        FALLBACK --> COLLECT
    end

    AG --> AGG[Aggregate Answers]
    AGG -->|final answer + sources| GR
    GR --> U

    ORCH -.->|embed + search| QD[(Qdrant<br/>vector store)]
    RW & SH & AGG -.->|checkpoint state| PG[(PostgreSQL<br/>LangGraph checkpointer)]
    ORCH -.->|generate| GROQ[Groq API<br/>LLM inference]

    style PG fill:#336791,color:#fff
    style QD fill:#dc244c,color:#fff
    style GROQ fill:#f55036,color:#fff
    style RL fill:#e8a33d,color:#000