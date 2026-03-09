import json
import uuid
import asyncio
import sqlite3
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from src.graph.state import get_detailed_research_status
from src.util.models import ResearchRequest
from src.worker.tasks import run_research_task
from src.graph.workflow import create_workflow 
from src.api.deps import get_conn # Keep for the 'clear-all' sync wipe
import random

research_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global research_app
    # Initialize the async checkpointer inside factory
    research_app = await create_workflow()    
    yield
    # If your checkpointer has a close method, call it here
    # await research_app.checkpointer.conn.close()

fastapi_app = FastAPI(title="Research AI", lifespan=lifespan)
@fastapi_app.get("/")
async def root():
    
    return {"message": "Status Ok"}

@fastapi_app.get("/health")
async def health():    
    return {"status": "ok"}

@fastapi_app.post("/research")
async def start_research(req: ResearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # Note: run_research_task must now use 'await research_app.ainvoke'
    background_tasks.add_task(run_research_task, job_id, req, app=research_app)
    
    return {
        "job_id": job_id,
        "status": "initiated",
        "stream_detailed_url": f"/stream_detailed/{job_id}",
        "stream_basic_url": f"/stream_basic/{job_id}",
        "stream_raw_url": f"/stream_raw/{job_id}"
    }

@fastapi_app.get("/status/{job_id}")
async def get_final_state(job_id: str):
    config = {"configurable": {"thread_id": job_id}}
    
    # FIX: Use aget_state (Async) instead of get_state (Sync)
    state = await research_app.aget_state(config)
    
    if not state.values:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "is_finished": len(state.next) == 0,
        "data": state.values
    }

@fastapi_app.get("/jobs/active")
async def list_active_jobs():
    
    active_jobs = []
    
    # Fetching all checkpoints from the async checkpointer
    # list() is an async generator in AsyncSqliteSaver
    async for checkpoint_tuple in research_app.checkpointer.alist(None):
        thread_id = checkpoint_tuple.config["configurable"]["thread_id"]
        
        config = {"configurable": {"thread_id": thread_id}}
        state = await research_app.aget_state(config)
        
        if state.next:
            active_jobs.append({
                "job_id": thread_id,
                "next_node": state.next[0],
                "values_summary": {
                    "sections_completed": len(state.values.get("sections_completed", []))
                }
            })
            
    return {"active_jobs": active_jobs, "count": len(active_jobs)}

@fastapi_app.post("/jobs/clear-all")
async def clear_all_jobs():
    try:
        def wipe_db():
            # Using your existing get_conn sync helper is fine for a raw delete
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints;")
            cursor.execute("DELETE FROM writes;")
            conn.commit()
            conn.close()

        await asyncio.to_thread(wipe_db)
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

@fastapi_app.get("/stream_basic/{job_id}")
async def stream_research(job_id: str, request: Request):
    
    global research_app

    async def event_generator():
        config = {"configurable": {"thread_id": job_id}}
        stream_it = research_app.astream(None, config=config, stream_mode="updates")
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    update = await asyncio.wait_for(anext(stream_it), timeout=60.0)
                    if not update: continue

                    node_name = list(update.keys())[0]
                    node_data = update[node_name]

                    payload = {
                        "node": node_name,
                        "status": "in_progress",
                        "sections_count": len(node_data.get("sections_completed", [])),
                    }

                    if "paper_path" in node_data and node_data["paper_path"] != None:
                        payload["status"] = "complete"
                        payload["path"] = node_data["paper_path"]
                        yield f"data: {json.dumps(payload)}\n\n"
                        break 

                    yield f"data: {json.dumps(payload)}\n\n"

                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'status': 'timeout'})}\n\n"
                    break
                except (StopAsyncIteration, StopIteration):
                    break
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'details': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@fastapi_app.get("/stream_detailed/{job_id}")
async def stream_research2(job_id: str, request: Request):
    global research_app

    async def event_generator():
        config = {"configurable": {"thread_id": job_id}}
        # We start the stream. Note: 'updates' gives us what just changed.
        stream_it = research_app.astream(None, config=config, stream_mode="updates")
        
        try:
            async for update in stream_it:
                if await request.is_disconnected():
                    break

                # 1. Identify which node just finished
                node_name = list(update.keys())[0]
                
                # 2. Fetch the FULL current state to run our analysis
                # This is necessary because 'update' only has partial data
                full_state_snapshot = await research_app.aget_state(config)
                current_state = full_state_snapshot.values
                
                # 3. Get detailed status using the function we wrote
                detailed_info = await get_detailed_research_status(current_state)
                
                # 4. Construct the payload
                payload = {
                    "node": node_name,
                    "phase": detailed_info["phase"],
                    "status_text": detailed_info["status"],
                    "progress": detailed_info["progress"],
                    "section_info": detailed_info.get("section_count", "N/A"),
                    "is_complete": False
                }

                # 5. Check for completion (Assembly Node)
                if node_name == "assembly" or ("paper_path" in current_state and current_state.get("paper_path") != None):
                    payload["is_complete"] = True
                    payload["path"] = current_state.get("paper_path")
                    yield f"data: {json.dumps(payload)}\n\n"
                    break 

                yield f"data: {json.dumps(payload)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'details': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@fastapi_app.get("/stream_raw/{job_id}")
async def stream_raw(job_id: str, request: Request):
    global research_app

    async def event_generator():
        config = {"configurable": {"thread_id": job_id}}
        
        # Use 'updates' to trigger a yield every time a node completes its work
        stream_it = research_app.astream(None, config=config, stream_mode="updates")
        
        try:
            async for update in stream_it:
                # Standard check for client disconnection
                if await request.is_disconnected():
                    break

                # Fetch the complete raw state snapshot
                full_state_snapshot = await research_app.aget_state(config)
                raw_state = full_state_snapshot.values
                
                # Identify which node just fired (the key in the update dict)
                last_node = list(update.keys())[0] if update else "unknown"

                # Check if the termination condition is met
                paper_path = raw_state.get("paper_path")
                is_complete = paper_path is not None

                payload = {
                    "node": last_node,
                    "raw_state": raw_state,
                    "is_complete": is_complete
                }

                yield f"data: {json.dumps(payload)}\n\n"

                if is_complete:
                    break

        except Exception as e:
            error_msg = {"status": "error", "details": str(e)}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

