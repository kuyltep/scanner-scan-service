from kafka import KafkaProducer
import json
from app_types.message_types import OutgoingMessage
from config.config import Config

class KafkaProducerHandler:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=Config.KAFKA_HOST,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

    def send_message(self, outgoing_message: OutgoingMessage):
        self.producer.send(Config.KAFKA_SEND_TOPIC, value=outgoing_message.to_dict())
        self.producer.flush()