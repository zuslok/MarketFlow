from kombu import Connection, Exchange, Producer

from .config import settings

exchange = Exchange(
    settings.rabbitmq_exchange,
    type="topic",
    durable=True
)

def publish_message(routing_key: str, payload: dict):
    with Connection(settings.rabbitmq_url) as conn:
        producer = Producer(conn)
        producer.publish(
            body=payload,
            exchange=exchange,
            routing_key=routing_key,
            declare=[exchange],
            serializer="json",
            delivery_mode=2 #persistent
        )