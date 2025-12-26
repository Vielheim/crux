import os
import aioboto3
from botocore.exceptions import ClientError

# Load Config
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


async def get_s3_client():
    """
    Async Context Manager for S3 Client.
    Usage: async with get_s3_client() as s3: ...
    """
    session = aioboto3.Session()
    return session.client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


async def upload_file_to_s3(file_obj, object_name: str) -> str:
    """
    Uploads a file-like object to S3/MinIO and returns the URL.
    """
    async with await get_s3_client() as s3:
        try:
            # upload_fileobj is efficient for large files as it streams data
            await s3.upload_fileobj(file_obj, S3_BUCKET_NAME, object_name)

            # Construct the URL (For local MinIO, this is usually acceptable)
            # In production S3, you might want to generate a presigned URL instead
            url = f"{AWS_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_name}"
            return url
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            raise e
