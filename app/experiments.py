# experiment management
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from sqlalchemy import func

from app.db import get_db
from app.models import Experiment, ExperimentVariant
from app.schemas import (
    ExperimentCreate,
    VariantCreate,
    ExperimentResponse,
    VariantResponse,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    payload: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
):
    experiment = Experiment(
        id=uuid4(),
        name=payload.name,
        target_segment_id=payload.target_segment_id,
        status=payload.status,
    )

    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)

    return experiment


@router.post("/{experiment_id}/variants", response_model=VariantResponse)
async def create_variant(
    experiment_id: UUID,
    payload: VariantCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Check current total weight
    result = await db.execute(
        select(func.sum(ExperimentVariant.weight)).where(
            ExperimentVariant.experiment_id == experiment_id
        )
    )
    current_weight = result.scalar() or 0

    if current_weight + payload.weight > 100:
        raise HTTPException(
            status_code=400,
            detail="Total variant weight cannot exceed 100",
        )

    variant = ExperimentVariant(
        id=uuid4(),
        experiment_id=experiment_id,
        name=payload.name,
        weight=payload.weight,
        config=payload.config,
    )

    db.add(variant)
    await db.commit()
    await db.refresh(variant)

    return variant


@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment))
    return result.scalars().all()

@router.get("/{experiment_id}/activate", response_model=ExperimentResponse)
async def activate_experiment(experiment_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment.status = "ACTIVE"
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)

    return experiment