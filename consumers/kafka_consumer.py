from kafka import KafkaConsumer
import json
from config.config import Config
from app_types.message_types import IncomingMessage

class KafkaConsumerHandler:
    def __init__(self):
        self.consumer = KafkaConsumer(
            Config.KAFKA_RECIEVE_TOPIC,
            bootstrap_servers=Config.KAFKA_HOST,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=Config.KAFKA_GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

    def consume_messages(self):
        for message in self.consumer:
            try:
                incoming_message = IncomingMessage.from_dict(message.value)
                yield incoming_message
            except Exception as e:
                print(f"Error parsing message: {e}")