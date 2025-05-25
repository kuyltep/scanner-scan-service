from minio import Minio
from config.config import Config

class MinioService:
    def __init__(self):
        print(Config.MINIO_ENDPOINT)
        self.client = Minio(
            Config.MINIO_ENDPOINT,
            access_key=Config.MINIO_ACCESS_KEY,
            secret_key=Config.MINIO_SECRET_KEY,
            secure=False 
        )

    def download_file(self, object_name, local_path):
        self.client.fget_object(Config.MINIO_BUCKET_SCANS, object_name, local_path)

    def upload_file(self, local_path, object_name, content_type):
        self.client.fput_object(Config.MINIO_BUCKET_RESULTS, object_name, local_path, content_type=content_type)
      
    def delete_file(self, object_name):
        self.client.remove_object(Config.MINIO_BUCKET_SCANS, object_name)