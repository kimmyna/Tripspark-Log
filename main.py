from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from fastapi import BackgroundTasks, FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from models.log import LogCreate, LogRead

# -----------------------------------------------------------------------------
# In-memory storage
# -----------------------------------------------------------------------------
logs: Dict[int, LogRead] = {}
_next_id: int = 1

app = FastAPI(
    title="TripSpark Log Microservice",
    description="Tracks user activity for TripSpark including places visited, ratings, and feedback.",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Background worker
# -----------------------------------------------------------------------------
def store_log(log: LogCreate) -> None:
    """
    Simulated asynchronous DB insert.
    """
    global _next_id

    log_id = _next_id
    _next_id += 1

    new_log = LogRead(
        id=log_id,
        created_at=datetime.utcnow(),
        **log.model_dump(),
    )
    logs[log_id] = new_log


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.post("/logs", status_code=202)
async def create_log(log: LogCreate, background_tasks: BackgroundTasks):
    """
    Accept a log entry asynchronously.
    Returns 202 Accepted immediately.
    """
    background_tasks.add_task(store_log, log)
    return {"status": "accepted"}


@app.get("/logs", response_model=List[LogRead])
def list_logs(
    user_id: Optional[UUID] = Query(None, description="Filter logs by user ID."),
    place_name: Optional[str] = Query(None, description="Filter logs by place name."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(10, ge=1, le=100, description="Pagination limit."),
):
    """
    List log entries with optional filtering and pagination.
    """
    results = list(logs.values())

    if user_id is not None:
        results = [l for l in results if l.user_id == user_id]

    if place_name is not None:
        results = [l for l in results if l.place_name == place_name]

    # Sort newest first
    results.sort(key=lambda x: x.created_at, reverse=True)

    return results[offset : offset + limit]


@app.get("/logs/{log_id}", response_model=LogRead)
def get_log(log_id: int = Path(..., description="Numeric ID of the log entry.")):
    """
    Retrieve a single log entry by ID.
    """
    log = logs.get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


# -----------------------------------------------------------------------------
# NEW: Root endpoint (so '/' doesn't show Not Found)
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "TripSpark Log Service Running"}

