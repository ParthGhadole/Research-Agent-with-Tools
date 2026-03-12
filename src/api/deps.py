import os
import sqlite3
import aiosqlite

db_folder = "db"

def get_conn():

    db_path = os.path.join(db_folder, "state_memory.db")

    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
        print(f"Created directory: {db_folder}")

    conn = sqlite3.connect(db_path, check_same_thread=False)    

    return conn

async def get_async_conn():
    db_path = os.path.join(db_folder, "state_memory.db")

    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
        print(f"Created directory: {db_folder}")

    # aiosqlite.connect is an async call
    conn = await aiosqlite.connect(db_path)
    
    # Enable WAL mode for high performance
    await conn.execute("PRAGMA journal_mode=WAL;")
    
    return conn

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def init_checkpointer():
    conn = await get_async_conn()
    
    # Pass the async connection here
    checkpointer = AsyncSqliteSaver(conn)
    
    # Important: This creates the hidden LangGraph tables in your DB
    await checkpointer.setup()
    
    return checkpointer

# ---------------------------------------------------------------------------
# Async job-store helpers (SQLite-backed, replaces the in-memory jobs dict)
# ---------------------------------------------------------------------------

async def init_jobs_table():
    """Create the jobs table if it doesn't exist. Call once at startup."""
    db_path = os.path.join(db_folder, "state_memory.db")

    if not os.path.exists(db_folder):
        os.makedirs(db_folder)

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id  TEXT PRIMARY KEY,
                status  TEXT NOT NULL DEFAULT 'initiated',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.commit()


async def _jobs_conn():
    """Return a raw aiosqlite connection to the shared DB."""
    db_path = os.path.join(db_folder, "state_memory.db")
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    return conn


async def job_set(job_id: str, status: str) -> None:
    """Insert or update a job's status."""
    async with aiosqlite.connect(os.path.join(db_folder, "state_memory.db")) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute(
            """
            INSERT INTO jobs (job_id, status, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(job_id) DO UPDATE
                SET status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
            """,
            (job_id, status),
        )
        await conn.commit()


async def job_get(job_id: str, default: str = "initializing") -> str:
    """Return the status for a job, or *default* if not found."""
    async with aiosqlite.connect(os.path.join(db_folder, "state_memory.db")) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        async with conn.execute(
            "SELECT status FROM jobs WHERE job_id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else default


async def job_all() -> dict[str, str]:
    """Return all jobs as {job_id: status}."""
    async with aiosqlite.connect(os.path.join(db_folder, "state_memory.db")) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        async with conn.execute("SELECT job_id, status FROM jobs") as cursor:
            rows = await cursor.fetchall()
    return {r[0]: r[1] for r in rows}


async def jobs_clear_all() -> None:
    """Delete every row from the jobs table."""
    async with aiosqlite.connect(os.path.join(db_folder, "state_memory.db")) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("DELETE FROM jobs;")
        await conn.commit()