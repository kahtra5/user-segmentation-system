# background worker
import asyncio
import aio_pika
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import AsyncSessionLocal
from app.models import UserMetrics
from app.segment_evaluator import evaluate_user_segments
from sqlalchemy import select

from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.models import UserMetrics, Order

RABBIT_QUEUE = "user_events"


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())

        user_id = data["user_id"]
        amount = data.get("amount", 0)

        async with AsyncSessionLocal() as db:

            # 1️⃣ Insert Order
            order = Order(
                user_id=user_id,
                amount=amount,
            )
            db.add(order)
            await db.commit()

            # 2️⃣ Fetch metrics row
            result = await db.execute(
                select(UserMetrics).where(UserMetrics.user_id == user_id)
            )
            metrics = result.scalar_one_or_none()

            if not metrics:
                return

            # 3️⃣ Define windows
            now = datetime.utcnow()
            window_23 = now - timedelta(days=23)
            window_7 = now - timedelta(days=7)
            window_30 = now - timedelta(days=30)

            # 4️⃣ Recalculate rolling counts

            result = await db.execute(
                select(func.count(Order.id)).where(
                    Order.user_id == user_id,
                    Order.created_at >= window_23
                )
            )
            orders_last_23 = result.scalar() or 0

            result = await db.execute(
                select(func.count(Order.id)).where(
                    Order.user_id == user_id,
                    Order.created_at >= window_7
                )
            )
            orders_last_7 = result.scalar() or 0

            result = await db.execute(
                select(func.count(Order.id)).where(
                    Order.user_id == user_id,
                    Order.created_at >= window_30
                )
            )
            orders_last_30 = result.scalar() or 0

            result = await db.execute(
                select(func.count(Order.id)).where(
                    Order.user_id == user_id
                )
            )
            total_orders = result.scalar() or 0

            result = await db.execute(
                select(func.sum(Order.amount)).where(
                    Order.user_id == user_id
                )
            )
            lifetime_value = result.scalar() or 0

            # 5️⃣ Update metrics row
            metrics.orders_last_23_days = orders_last_23
            metrics.orders_last_7_days = orders_last_7
            metrics.orders_last_30_days = orders_last_30
            metrics.total_orders = total_orders
            metrics.lifetime_value = lifetime_value

            await db.commit()

            # 6️⃣ Re-evaluate segments
            await evaluate_user_segments(user_id, db)


async def connect_with_retry():
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            print("Connected to RabbitMQ")
            return connection
        except Exception as e:
            print("RabbitMQ not ready, retrying in 3 seconds...")
            await asyncio.sleep(3)

async def main():
    connection = await connect_with_retry()
    channel = await connection.channel()

    queue = await channel.declare_queue(RABBIT_QUEUE, durable=True)

    await queue.consume(process_message)

    print("Worker started...")
    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())