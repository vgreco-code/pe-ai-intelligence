"""Job tracking endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import get_db
from models.job import AgentJob
from schemas.job import JobResponse
from typing import List
import json
import asyncio

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    """List all jobs"""
    jobs = db.query(AgentJob).order_by(AgentJob.created_at.desc()).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status"""
    job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


# Store active WebSocket connections for real-time updates
active_connections = {}


@router.websocket("/ws/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time job progress"""
    await websocket.accept()

    try:
        # Store connection
        if job_id not in active_connections:
            active_connections[job_id] = []
        active_connections[job_id].append(websocket)

        # Send initial job status
        job = db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if job:
            await websocket.send_json(
                {
                    "type": "status",
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "completed_companies": job.completed_companies,
                    "total_companies": job.total_companies,
                }
            )

        # Keep connection alive and listen for updates
        while True:
            # Wait a bit before checking again
            await asyncio.sleep(2)

            # Refresh job status
            db.expire_all()
            job = db.query(AgentJob).filter(AgentJob.id == job_id).first()

            if job:
                await websocket.send_json(
                    {
                        "type": "progress",
                        "job_id": job_id,
                        "status": job.status,
                        "progress": job.progress,
                        "completed_companies": job.completed_companies,
                        "total_companies": job.total_companies,
                    }
                )

                # Stop if job is complete or failed
                if job.status in ["completed", "failed"]:
                    break

    except WebSocketDisconnect:
        if job_id in active_connections:
            active_connections[job_id].remove(websocket)
            if not active_connections[job_id]:
                del active_connections[job_id]
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})


async def broadcast_job_update(job_id: str, message: dict):
    """Broadcast job update to all connected clients"""
    if job_id in active_connections:
        disconnected = []
        for connection in active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            active_connections[job_id].remove(conn)
