import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    KAFKA_HOST = os.getenv("KAFKA_HOST")
    KAFKA_RECIEVE_TOPIC = os.getenv("KAFKA_RECIEVE_TOPIC")
    KAFKA_SEND_TOPIC = os.getenv("KAFKA_SEND_TOPIC")
    KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID")

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_SCANS = os.getenv("MINIO_BUCKET_SCANS")
    MINIO_BUCKET_RESULTS = os.getenv("MINIO_BUCKET_RESULTS")