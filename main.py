from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from models.log import LogCreate, LogRead

# -----------------------------------------------------------------------------
# In-memory "database" (to be replaced by Cloud SQL later)
# -----------------------------------------------------------------------------
logs: Dict[int, LogRead] = {}
_next_id: int = 1

app = FastAPI(
    title="TripSpark Log Microservice",
    description=(
        "Tracks user activity for TripSpark, such as visited places, "
        "ratings, and feedback."
    ),
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Background worker (simulated async write)
# -----------------------------------------------------------------------------
def store_log(log: LogCreate) -> None:
    """
    Simulate an asynchronous write to a database.

    For Sprint 2, we keep this in-memory. Later, this function can be
    updated to insert into Cloud SQL without changing the API.
    """
    global _next_id

    log_id = _next_id
    _next_id += 1

    log_read = LogRead(
        id=log_id,
        created_at=datetime.utcnow(),
        **log.model_dump(),
    )
    logs[log_id] = log_read


# -----------------------------------------------------------------------------
# Log endpoints
# -----------------------------------------------------------------------------
@app.post("/logs", status_code=202)
async def create_log(log: LogCreate, background_tasks: BackgroundTasks):
    """
    Accept a log entry asynchronously.

    Returns:
        202 Accepted immediately, while the actual persistence is done in a
        background task.
    """
    background_tasks.add_task(store_log, log)
    return JSONResponse(status_code=202, content={"status": "accepted"})


@app.get("/logs", response_model=List[LogRead])
def list_logs(
    user_id: Optional[UUID] = Query(
        None,
        description="Filter logs by user ID.",
    ),
    place_name: Optional[str] = Query(
        None,
        description="Filter logs by place name.",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Pagination offset (zero-based index into the result set).",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Pagination limit (maximum number of items to return).",
    ),
):
    """
    List log entries with optional filtering and pagination.

    - Filter by `user_id` (UUID) and/or `place_name`.
    - Use `offset` + `limit` for pagination.
    """
    # Start from all logs
    results: List[LogRead] = list(logs.values())

    # Optional filters
    if user_id is not None:
        results = [l for l in results if l.user_id == user_id]

    if place_name is not None:
        results = [l for l in results if l.place_name == place_name]

    # Sort newest first
    results.sort(key=lambda l: l.created_at, reverse=True)

    # Apply pagination
    sliced = results[offset : offset + limit]
    return sliced


@app.get("/logs/{log_id}", response_model=LogRead)
def get_log(
    log_id: int = Path(
        ...,
        description="Numeric ID of the log entry.",
    )
):
    """
    Retrieve a single log entry by its numeric ID.
    """
    log = logs.get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

