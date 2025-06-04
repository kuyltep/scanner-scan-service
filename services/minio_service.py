from minio import Minio
from config.config import Config
import json

class MinioService:
    def __init__(self):
        print(Config.MINIO_ENDPOINT)
        self.client = Minio(
            Config.MINIO_ENDPOINT,
            access_key=Config.MINIO_ACCESS_KEY,
            secret_key=Config.MINIO_SECRET_KEY,
            secure=False 
        )
        # Ensure results bucket has public read policy
        self._setup_public_read_policy()

    def _setup_public_read_policy(self):
        """Set up public read policy for results bucket"""
        try:
            bucket_name = Config.MINIO_BUCKET_RESULTS
            
            # Check if bucket exists, create if not
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            # Public read policy for results bucket
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                        "Resource": f"arn:aws:s3:::{bucket_name}"
                    },
                    {
                        "Effect": "Allow", 
                        "Principal": {"AWS": "*"},
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            self.client.set_bucket_policy(bucket_name, json.dumps(policy))
            print(f"Public read policy set for bucket: {bucket_name}")
            
        except Exception as e:
            print(f"Warning: Could not set public read policy: {e}")

    def download_file(self, object_name, local_path):
        self.client.fget_object(Config.MINIO_BUCKET_SCANS, object_name, local_path)

    def upload_file(self, local_path, object_name, content_type):
        """Upload file with public read access"""
        result = self.client.fput_object(
            Config.MINIO_BUCKET_RESULTS, 
            object_name, 
            local_path, 
            content_type=content_type
        )
        print(f"Uploaded {object_name} with public read access")
        return result

    def delete_file(self, object_name):
        self.client.remove_object(Config.MINIO_BUCKET_SCANS, object_name)