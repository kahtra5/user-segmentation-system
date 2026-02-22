from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    UserSegment,
    Experiment,
    ExperimentVariant,
    ExperimentAssignment,
)
from app.assignment_engine import assign_variant
from uuid import UUID

import json
from app.cache import redis_client

CACHE_TTL = 60  # Seconds

async def get_user_experiments(user_id: UUID, db: AsyncSession):

    cache_key = f"experiments:{user_id}"

    cached=await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)



    # 1️⃣ Fetch user segment IDs
    result = await db.execute(
        select(UserSegment.segment_id).where(UserSegment.user_id == user_id)
    )
    segment_ids = result.scalars().all()

    if not segment_ids:
        return []

    # 2️⃣ Fetch active experiments targeting these segments
    result = await db.execute(
        select(Experiment).where(
            Experiment.target_segment_id.in_(segment_ids),
            Experiment.status == "ACTIVE",
        )
    )
    experiments = result.scalars().all()

    response = []

    for experiment in experiments:
        # 3️⃣ Check existing assignment
        result = await db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.user_id == user_id,
                ExperimentAssignment.experiment_id == experiment.id,
            )
        )
        assignment = result.scalar_one_or_none()

        if assignment:
            response.append(
                {
                    "experiment_id": str(experiment.id),
                    "variant_id": str(assignment.variant_id),
                }
            )
            continue

        # 4️⃣ Fetch variants
        result = await db.execute(
            select(ExperimentVariant).where(
                ExperimentVariant.experiment_id == experiment.id
            )
        )
        variants = result.scalars().all()

        if not variants:
            continue

        # 5️⃣ Deterministic assignment
        chosen_variant = assign_variant(
            str(user_id),
            str(experiment.id),
            variants,
        )

        new_assignment = ExperimentAssignment(
            user_id=user_id,
            experiment_id=experiment.id,
            variant_id=chosen_variant.id,
        )

        db.add(new_assignment)

        response.append(
            {
                "experiment_id": str(experiment.id),
                "variant_id": str(chosen_variant.id),
            }
        )

    await db.commit()

    return response