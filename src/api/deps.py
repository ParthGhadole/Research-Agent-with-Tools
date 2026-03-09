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