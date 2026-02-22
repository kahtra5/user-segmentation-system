# segmentation logic
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Segment
from app.schemas import SegmentCreate, SegmentResponse
import uuid

router = APIRouter(prefix="/segments", tags=["segments"])


@router.post("/", response_model=SegmentResponse)
async def create_segment(
    payload: SegmentCreate,
    db: AsyncSession = Depends(get_db),
):
    segment = Segment(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        rule_definition=payload.rule_definition.model_dump(),
    )

    db.add(segment)
    await db.commit()
    await db.refresh(segment)

    return segment


@router.get("/", response_model=list[SegmentResponse])
async def list_segments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Segment))
    return result.scalars().all()