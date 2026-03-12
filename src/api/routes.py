import json
import uuid
import asyncio
import hashlib
import random

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from src.graph.state import get_detailed_research_status
from src.util.models import ResearchPayload
from src.worker.tasks import run_research_task
from src.graph.workflow import create_workflow
from src.api.deps import (
    get_conn,
    init_jobs_table,
    job_get,
    job_set,
    job_all,
    jobs_clear_all,
)

research_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global research_app

    # 1. Ensure the jobs table exists before anything else
    await init_jobs_table()

    # 2. Initialize the workflow and the DB connection
    research_app = await create_workflow()
    print("Workflow initialized with AsyncSqliteSaver.")

    yield

    # 3. Cleanup: Close the sqlite connection on shutdown
    if research_app and research_app.checkpointer:
        await research_app.checkpointer.conn.close()
        print("AsyncSqliteSaver connection closed.")


fastapi_app = FastAPI(title="Research AI", lifespan=lifespan)


@fastapi_app.get("/")
async def root():
    return {"message": "Status Ok"}


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


@fastapi_app.post("/research/start")
async def start_research_background_task(req: ResearchPayload, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    await job_set(job_id, "initiated")
    background_tasks.add_task(run_research_task, job_id, req, app=research_app)
    return {
        "job_id": job_id,
        "status": "initiated",
        "get_status_at": f"/research/jobs/{job_id}",
        "get_limited_stream_at": f"/research/jobs/{job_id}/stream",
        "get_live_feed_at": f"/research/jobs/{job_id}/feed",
        "get_live_updates_at": f"/research/jobs/{job_id}/events"
    }


@fastapi_app.get("/research/jobs/{job_id}")
async def get_background_research_status(job_id: str):
    config = {"configurable": {"thread_id": job_id}}
    status = await job_get(job_id, "initializing")
    try:
        full_state_snapshot = await research_app.aget_state(config)
        current_state = full_state_snapshot.values

        if not current_state:
            return {
                "job_id": job_id,
                "status": "initializing",
                "state_details": None,
                "message": "Job initialized but no state data recorded yet."
            }

        details = await get_detailed_research_status(current_state)

        has_error = current_state.get("error") is not None
        is_finished = current_state.get("output") is not None

        if has_error:
            status = "failed"
        elif is_finished:
            status = "complete"
        else:
            status = "in_progress"

        return {
            "job_id": job_id,
            "status": status,
            "state_details": details,
        }

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "data": "job_id not found or internal processing error"
        }
    finally:
        await job_set(job_id, status)


@fastapi_app.get("/research/jobs/{job_id}/stream")
async def preview_background_research_status(
    job_id: str,
    request: Request,
    interval_seconds: int = 10,
    num_updates: int = 6
):
    config = {"configurable": {"thread_id": job_id}}
    interval = interval_seconds

    async def event_generator():
        for _ in range(num_updates):
            if await request.is_disconnected():
                break
            status = await job_get(job_id, "initializing")
            try:
                full_state_snapshot = await research_app.aget_state(config)
                current_state = full_state_snapshot.values

                if not current_state:
                    data = {
                        "job_id": job_id,
                        "status": "initializing",
                        "message": "No state data recorded yet."
                    }
                else:
                    details = await get_detailed_research_status(current_state)
                    has_error = current_state.get("error") is not None
                    is_finished = current_state.get("output") is not None

                    status = "in_progress"
                    if has_error:
                        status = "failed"
                    elif is_finished:
                        status = "complete"

                    data = {
                        "job_id": job_id,
                        "status": status,
                        "state_details": details,
                    }

                yield f"data: {json.dumps(data)}\n\n"

                if status in ["complete", "failed"]:
                    break

            except Exception as e:
                err_data = {
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e),
                    "data": "job_id not found or internal processing error"
                }
                yield f"data: {json.dumps(err_data)}\n\n"
                break
            finally:
                await job_set(job_id, status)

            await asyncio.sleep(interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@fastapi_app.get("/research/jobs/{job_id}/feed")
async def stream_background_research_status(job_id: str, request: Request, interval: int = 5):
    config = {"configurable": {"thread_id": job_id}}

    async def event_generator():
        status = await job_get(job_id, "initializing")

        while True:
            if await request.is_disconnected():
                break

            try:
                full_state_snapshot = await research_app.aget_state(config)
                current_state = full_state_snapshot.values

                if not current_state:
                    data = {
                        "job_id": job_id,
                        "status": "initializing",
                        "message": "Waiting for process to start..."
                    }
                else:
                    details = await get_detailed_research_status(current_state)
                    has_error = current_state.get("error") is not None
                    is_finished = current_state.get("output") is not None

                    status = "in_progress"
                    if has_error:
                        status = "failed"
                    elif is_finished:
                        status = "complete"

                    data = {
                        "job_id": job_id,
                        "status": status,
                        "state_details": details,
                    }

                yield f"data: {json.dumps(data)}\n\n"

                if status in ["complete", "failed"]:
                    break

            except Exception as e:
                status = "error"
                err_data = {
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(err_data)}\n\n"
                break

            finally:
                await job_set(job_id, status)

            await asyncio.sleep(interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@fastapi_app.get("/research/jobs/stream/{job_id}/events")
async def stream_updates_background_research_status(job_id: str, request: Request, interval: int = 3):
    config = {"configurable": {"thread_id": job_id}}
    if interval <= 2:
        interval = 5

    async def event_generator():
        last_state_hash = None
        status = "initializing"

        while True:
            if await request.is_disconnected():
                break

            try:
                full_state_snapshot = await research_app.aget_state(config)
                current_state = full_state_snapshot.values

                if current_state:
                    state_str = json.dumps(current_state, sort_keys=True, default=str)
                    current_hash = hashlib.md5(state_str.encode()).hexdigest()

                    if current_hash != last_state_hash:
                        details = await get_detailed_research_status(current_state)
                        has_error = current_state.get("error") is not None
                        is_finished = current_state.get("output") is not None

                        status = "in_progress"
                        if has_error:
                            status = "failed"
                        elif is_finished:
                            status = "complete"

                        data = {
                            "job_id": job_id,
                            "status": status,
                            "state_details": details,
                        }

                        yield f"data: {json.dumps(data)}\n\n"

                        last_state_hash = current_hash
                        await job_set(job_id, status)

                        if status in ["complete", "failed"]:
                            break

            except Exception as e:
                err_data = {"job_id": job_id, "status": "error", "error": str(e)}
                yield f"data: {json.dumps(err_data)}\n\n"
                break

            finally:
                await job_set(job_id, status)

            await asyncio.sleep(interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@fastapi_app.get("/research/state/{job_id}")
async def get_background_research_state(job_id: str):
    try:
        config = {"configurable": {"thread_id": job_id}}
        response = await research_app.aget_state(config)
        state = response.values

        if not state:
            return {
                "job_id": job_id,
                "status": "initializing",
                "message": "Job found but no state values recorded yet.",
                "raw_state": {},
                "state_details": None
            }

        details = await get_detailed_research_status(state)

        status = "in_progress"
        if not response.next:
            status = "complete"
        if state.get("error"):
            status = "failed"

        return {
            "job_id": job_id,
            "status": status,
            "state_details": details,
            "raw_state": state,
            "next_step": response.next[0] if response.next else None
        }

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "data": "job_id not found or internal processing error"
        }


@fastapi_app.get("/jobs/active")
async def list_jobs():
    all_jobs = await job_all()
    return {"all_current_jobs": all_jobs if all_jobs else None}


@fastapi_app.post("/jobs/clear-all")
async def clear_all_jobs():
    try:
        def wipe_db():
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints;")
            cursor.execute("DELETE FROM writes;")
            conn.commit()
            conn.close()

        await asyncio.to_thread(wipe_db)
        await jobs_clear_all()
        return {"status": "success", "message": "All states cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@fastapi_app.get("/test-random-stream")
async def random_stream():
    """Streams a random number every 10 seconds for 1 minute."""
    async def event_generator():
        for i in range(6):
            await asyncio.sleep(5)
            data = {
                "iteration": i + 1,
                "number": random.randint(1, 100),
                "timestamp": str(asyncio.get_event_loop().time())
            }
            yield f"data: {json.dumps(data)}\n\n"

        yield "data: {\"status\": \"end\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")