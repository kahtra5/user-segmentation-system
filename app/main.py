from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_db
from app.segments import router as segments_router

from app.segment_evaluator import evaluate_user_segments
from uuid import UUID

app = FastAPI()

app.include_router(segments_router)

@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db_status": result.scalar()}


@app.post("/evaluate/{user_id}")
async def evaluate(user_id: UUID, db: AsyncSession = Depends(get_db)):
    segments = await evaluate_user_segments(user_id, db)
    return {"assigned_segments": segments}