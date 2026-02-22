import aio_pika
from app.config import settings
import json

RABBIT_QUEUE = "user_events"


async def get_rabbit_connection():
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)


async def publish_event(message: dict):
    connection = await get_rabbit_connection()
    channel = await connection.channel()

    queue = await channel.declare_queue(RABBIT_QUEUE, durable=True)

    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=RABBIT_QUEUE,
    )

    await connection.close()