import boto3
from botocore.exceptions import ClientError
import cred
import os
import mimetypes
import hashlib

class S3Manager:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=cred.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=cred.AWS_SECRET_ACCESS_KEY,
            region_name=cred.AWS_REGION,
        )
        self.bucket = cred.S3_BUCKET

    def list_prefix(self, prefix=""):
        """Return folders and files under a prefix"""
        folders, files = set(), []
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter="/")
            if "CommonPrefixes" in response:
                folders = {p["Prefix"] for p in response["CommonPrefixes"]}
            if "Contents" in response:
                files = [obj["Key"] for obj in response["Contents"] if not obj["Key"].endswith("/")]
        except ClientError as e:
            print("Error listing prefix:", e)
        return sorted(folders), sorted(files)

    def upload_file(self, local_path, s3_path):
        """Upload one file with correct MIME type and SHA256 checksum"""
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = "application/octet-stream"

        # Calculate SHA256 hash (optional, just for logging)
        sha256_hash = hashlib.sha256()
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        checksum_sha256 = sha256_hash.hexdigest()

        try:
            with open(local_path, "rb") as f:
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=s3_path,
                    Body=f,
                    ContentType=content_type,
                    ChecksumAlgorithm="SHA256",
                )
            print(f"Uploaded {local_path} → s3://{self.bucket}/{s3_path} with SHA256 {checksum_sha256}")
        except ClientError as e:
            print("Upload failed:", e)

    def download_file(self, s3_key, local_path):
        """Download a single S3 file"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3.download_file(self.bucket, s3_key, local_path)
            print(f"Downloaded s3://{self.bucket}/{s3_key} → {local_path}")
        except ClientError as e:
            print("Download failed:", e)

    def delete_objects(self, keys):
        """Delete multiple objects"""
        try:
            delete_keys = [{"Key": key} for key in keys]
            self.s3.delete_objects(Bucket=self.bucket, Delete={"Objects": delete_keys})
            print(f"Deleted {len(keys)} objects from {self.bucket}")
        except ClientError as e:
            print("Deletion failed:", e)

    def create_folder(self, folder_name):
        """Create an empty folder"""
        if not folder_name.endswith("/"):
            folder_name += "/"
        try:
            self.s3.put_object(Bucket=self.bucket, Key=folder_name)
            print(f"Created folder {folder_name}")
        except ClientError as e:
            print("Folder creation failed:", e)

    def get_object_url(self, key):
        """Public object URL"""
        region = cred.AWS_REGION
        return f"https://{self.bucket}.s3.{region}.amazonaws.com/{key}"
