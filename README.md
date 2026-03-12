# Research AI

A multi-agent research orchestration system built with **LangGraph** and **FastAPI**, with a **Streamlit** frontend for monitoring and control. This application automates the process of planning, researching, and assembling comprehensive research papers using an iterative, node-based workflow with persistent state management.

---

## Project Structure

```text
├── app/
│   └── app.py                   # Streamlit frontend (monitoring + job control UI)
├── db/                          # Auto-generated on first run
│   └── state_memory.db          # SQLite checkpointer (persistence layer)
├── output/                      # Auto-generated on first run
│   └── Paper_<uuid>.md          # Final assembled research paper per job
├── src/
│   ├── api/
│   │   ├── deps.py              # Database connection helpers (Sync/Async)
│   │   └── routes.py            # FastAPI SSE and research route definitions
│   ├── graph/
│   │   ├── nodes/
│   │   │   ├── input_node.py           # Validates and ingests the research request
│   │   │   ├── planner_node.py         # Architects the research outline and section plan
│   │   │   ├── research_node.py        # Orchestrates web search and crawl tool calls
│   │   │   ├── tool_node.py            # Executes bound tools (search + crawl)
│   │   │   ├── context_summary_node.py # Summarizes accumulated raw research context
│   │   │   ├── section_summary_node.py # Produces per-section knowledge summaries
│   │   │   ├── builder_node.py         # Iterative section drafting agent
│   │   │   └── assembly_node.py        # Final compilation of all sections into output
│   │   ├── state.py             # Graph state definitions and status helpers
│   │   └── workflow.py          # LangGraph blueprint and checkpointer setup
│   ├── tools/
│   │   ├── web_search_tool.py   # Web search tool binding     
│   │   └── web_crawl_tool.py    # Web page crawl tool binding
│   ├── util/
│   │   ├── models.py            # Pydantic schemas for API requests
│   │   ├── llm_util.py          # LLM config and provider initialization
│   │   ├── summary_util.py      # Global summary formatting for prompts
│   │   └── prompts.py           # System prompts for all research agents
│   └── worker/
│       └── tasks.py             # Background task orchestration
├── main.py                      # FastAPI application entry point
├── pyproject.toml               # Dependency management (uv)
└── uv.lock                      # Lockfile for reproducible builds
```

---

## Key Features

### Multi-Agent Graph with Research Tools

The pipeline runs through a sequence of specialized LangGraph nodes:

- **Input** -- Validates and structures the incoming research request
- **Planner** -- Designs the full section outline based on the request
- **Research** -- Decides what to search and crawl, calling tools iteratively
- **Tool** -- Executes the bound web search and crawl tools
- **Context Summary** -- Compresses accumulated raw research into a usable context window
- **Builder** -- Drafts each section iteratively using the summarized knowledge
- **Section Summary** -- Produces a focused knowledge summary per section after drafting section and updates global summary
- **Assembly** -- Compiles all drafted sections into the final output paper

### Self-Healing Persistence

Uses **AsyncSqliteSaver** stored in the `db/` directory. The application automatically creates the `db/` folder on import and initializes the necessary LangGraph tables on startup.

If the server restarts mid-job, jobs can be resumed, their execution history remains intact, and they can be queried using the same `job_id`.

### High-Performance DB

Database connections use **aiosqlite** with write-ahead logging enabled:

```sql
PRAGMA journal_mode=WAL;
```

### Granular Streaming (SSE)

Three streaming modes are provided for real-time monitoring:

- **Limited Stream** -- Polls at a fixed interval for a set number of updates
- **Live Feed** -- Runs continuously until the job reaches a terminal state
- **Events (Delta)** -- Emits only when state actually changes, using MD5 hashing to detect transitions

### Streamlit Frontend

A dark-themed monitoring dashboard in `app/app.py` providing:

- Job submission with full configuration control
- Live progress visualization with per-node and per-section tracking
- All three streaming modes accessible from the UI
- Jobs dashboard with metrics, status table, and a drill-down inspector

---

> **Important**
>
> This project uses a custom LLM `.whl` library imported in `src/util/llm_util.py`.
> Inside this file there is an `if / elif` provider selection block that determines
> which LLM client is created based on the `provider` field in the request.
>
> The example request below assumes that the specified `provider` and `model` are
> already supported in that block.
>
> If you want to use a different provider or model, you must modify the `if / elif`
> logic in `llm_util.py` to add the corresponding initialization code before running.
>
> Langchain Gemini models are supported by default.
> Also update streamlit dropbox for provider with the newly supported provider.

---

## API Endpoints

### Research

**Start a research job**
```http
POST /research/start
```
Accepts a `ResearchPayload` and returns a `job_id` with links to all monitoring endpoints.

**Get job status and state details**
```http
GET /research/jobs/{job_id}
```
Returns the current status, execution phase, progress percentage, and full structured state details.

**Get raw graph state**
```http
GET /research/state/{job_id}
```
Returns the complete raw LangGraph state snapshot including `next_step` and all state fields.

---

### Real-time Monitoring (SSE)

**Limited stream** -- fixed number of updates at a set interval
```http
GET /research/jobs/{job_id}/stream?interval_seconds=10&num_updates=6
```

**Live feed** -- continuous polling until terminal state
```http
GET /research/jobs/{job_id}/feed?interval=5
```

**Events (delta only)** -- emits only when state changes
```http
GET /research/jobs/stream/{job_id}/events?interval=3
```

---

### Job Management

**List all active jobs**
```http
GET /jobs/active
```

**Clear all jobs and checkpoints**
```http
POST /jobs/clear-all
```
Hard-wipes all checkpoints and writes from the database.

**Health check**
```http
GET /health
GET /
```

---

## Setup and Installation

This project is optimized for **uv**.

### Install Dependencies

```bash
uv sync
```

### Environment Configuration

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_key_here
SERP_API_KEY = your_key_here
```

The `db/` and `output/` directories are created automatically on first run.

---

## Running the Project

### API Server -- Development

```bash
uv run python main.py
```

Starts Uvicorn with auto-reload enabled. The `main.py` entry point:

```python
def main():
    import uvicorn
    uvicorn.run("src.api.routes:fastapi_app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
```

### API Server -- Production

```bash
uv run uvicorn src.api.routes:fastapi_app --host 0.0.0.0 --port 8000 --workers 4
```

| Mode | Command | Reload | Workers |
|---|---|---|---|
| Development | `uv run python main.py` | Yes | 1 |
| Production | `uv run uvicorn ... --workers 4` | No | 4 |

Hot reload and multiple workers are mutually exclusive. Use `main.py` for development and the direct uvicorn command for deployment.

### Streamlit Frontend

With the API server running, start the frontend from the project root:

```bash
uv run streamlit run app/app.py
```

The dashboard connects to `http://127.0.0.1:8000` by default.

---

## Example Usage

### Start a Research Job

```http
POST /research/start
Content-Type: application/json
```

Request body:

```json
{
    "user_req": {
        "topic": "Graphene-based Supercapacitors",
        "description": "Comprehensive technical paper",
        "points_to_include": ["charge cycles", "thermal stability"],
        "min_sections": 4,
        "compulsory_headings": ["Introduction", "Abstract", "Conclusion"]
    },
    "config": {
        "llm": {
            "model": "gemini-2.5-flash",
            "provider": "google",
            "max_tokens": 3000
        },
        "graph": {
            "research_enabled": true,
            "max_web_search_limit": 5,
            "max_web_crawl_limit": 10,
            "keep_raw_crawl": true
        },
        "debug": false
    }
}
```

Example with curl:

```bash
curl -X POST "http://localhost:8000/research/start" \
-H "Content-Type: application/json" \
-d '{
    "user_req": {
        "topic": "Graphene-based Supercapacitors",
        "description": "Comprehensive technical paper",
        "points_to_include": ["charge cycles", "thermal stability"],
        "min_sections": 4,
        "compulsory_headings": ["Introduction", "Abstract", "Conclusion"]
    },
    "config": {
        "llm": {
            "model": "gemini-2.5-flash",
            "provider": "google",
            "max_tokens": 3000
        },
        "graph": {
            "research_enabled": true,
            "max_web_search_limit": 5,
            "max_web_crawl_limit": 10,
            "keep_raw_crawl": true
        },
        "debug": false
    }
}'
```

Example response:

```json
{
    "job_id": "e4a3039c-865b-42ed-b0dd-8118986c367c",
    "status": "initiated",
    "get_status_at": "/research/jobs/e4a3039c-865b-42ed-b0dd-8118986c367c",
    "get_limited_stream_at": "/research/jobs/e4a3039c-865b-42ed-b0dd-8118986c367c/stream",
    "get_live_feed_at": "/research/jobs/e4a3039c-865b-42ed-b0dd-8118986c367c/feed",
    "get_live_updates_at": "/research/jobs/e4a3039c-865b-42ed-b0dd-8118986c367c/events"
}
```

Use the returned `job_id` to monitor progress:

```bash
# Single status fetch
GET /research/jobs/{job_id}

# Limited stream (6 updates, 10s interval)
GET /research/jobs/{job_id}/stream?interval_seconds=10&num_updates=6

# Continuous live feed
GET /research/jobs/{job_id}/feed?interval=5

# Delta events only
GET /research/jobs/stream/{job_id}/events?interval=3
```

The final paper is saved to:

```
output/Paper_<uuid>.md
```