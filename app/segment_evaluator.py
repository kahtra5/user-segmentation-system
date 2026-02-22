from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Segment, UserMetrics, UserSegment
from app.rule_engine import evaluate_rule_group
import uuid


async def evaluate_user_segments(user_id: uuid.UUID, db: AsyncSession):
    # Remove existing assignments
    await db.execute(
        delete(UserSegment).where(UserSegment.user_id == user_id)
    )

    # Fetch user metrics
    result = await db.execute(
        select(UserMetrics).where(UserMetrics.user_id == user_id)
    )
    user_metrics = result.scalar_one_or_none()

    if not user_metrics:
        await db.commit()
        return []

    user_data = {
        "total_orders": user_metrics.total_orders,
        "orders_last_7_days": user_metrics.orders_last_7_days,
        "orders_last_23_days": user_metrics.orders_last_23_days,
        "orders_last_30_days": user_metrics.orders_last_30_days,
        "lifetime_value": float(user_metrics.lifetime_value),
        "location": user_metrics.location,
    }

    result = await db.execute(
        select(Segment).where(Segment.is_active == True)
    )
    segments = result.scalars().all()

    assigned_segments = []

    for segment in segments:
        if evaluate_rule_group(segment.rule_definition, user_data):
            db.add(
                UserSegment(
                    user_id=user_id,
                    segment_id=segment.id,
                )
            )
            assigned_segments.append(segment.id)

    await db.commit()

    return assigned_segments