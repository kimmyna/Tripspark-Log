from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text

from models.log import LogCreate, LogRead
from db import engine

app = FastAPI(
    title="TripSpark Log Microservice",
    description="Tracks user activity for TripSpark including places visited, ratings, and feedback. Backed by Cloud SQL.",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# Background worker: insert into DB
# -----------------------------------------------------------------------------
def store_log_db(log: LogCreate) -> None:
    """
    Asynchronously insert a log row into the Cloud SQL database.
    """
    with engine.begin() as conn:
        stmt = text(
            """
            INSERT INTO logs (user_id, user_name, place_name, rating, feedback, action)
            VALUES (:user_id, :user_name, :place_name, :rating, :feedback, :action)
            """
        )
        params = {
            "user_id": str(log.user_id),
            "user_name": log.user_name,
            "place_name": log.place_name,
            "rating": log.rating,
            "feedback": log.feedback,
            "action": log.action,
        }
        conn.execute(stmt, params)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.post("/logs", status_code=202)
async def create_log(log: LogCreate, background_tasks: BackgroundTasks):
    """
    Accept a log entry asynchronously.
    Returns 202 Accepted immediately while the DB insert happens in the background.
    """
    background_tasks.add_task(store_log_db, log)
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
    Backed by Cloud SQL.
    """
    query = """
        SELECT id, user_id, user_name, place_name, rating, feedback, action, created_at
        FROM logs
        WHERE 1=1
    """
    params: dict = {}

    if user_id is not None:
        query += " AND user_id = :user_id"
        params["user_id"] = str(user_id)

    if place_name is not None:
        query += " AND place_name = :place_name"
        params["place_name"] = place_name

    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    # rows는 dict-like 객체 리스트이므로 그대로 Pydantic에 넣어줌
    return [LogRead(**row) for row in rows]


@app.get("/logs/{log_id}", response_model=LogRead)
def get_log(
    log_id: int = Path(..., description="Numeric ID of the log entry.")
):
    """
    Retrieve a single log entry by ID from Cloud SQL.
    """
    query = """
        SELECT id, user_id, user_name, place_name, rating, feedback, action, created_at
        FROM logs
        WHERE id = :id
    """

    with engine.connect() as conn:
        row = conn.execute(text(query), {"id": log_id}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Log not found")

    return LogRead(**row)


# -----------------------------------------------------------------------------
# DB connection test endpoint
# -----------------------------------------------------------------------------
@app.get("/dbtest")
def test_db_connection():
    """
    Simple endpoint to verify Cloud SQL connectivity.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar_one()
        return {"status": "success", "result": int(result)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Root endpoint (health)
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "TripSpark Log Service Running (DB-backed)"}
