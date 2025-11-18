import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import uuid
from datetime import datetime, timedelta
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class S3Service:
    """Service for handling AWS S3 operations."""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_BUCKET_NAME

    def upload_file(
        self,
        file: BinaryIO,
        folder: str,
        filename: str,
        content_type: str
    ) -> Optional[str]:
        """
        Upload a file to S3.

        Args:
            file: File object to upload
            folder: Folder path in S3 (e.g., 'videos', 'transcripts')
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            S3 URL of the uploaded file or None if failed
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            s3_key = f"{folder}/{unique_filename}"

            logger.info(f"Starting S3 upload: {filename} -> {s3_key}")
            logger.info(f"Bucket: {self.bucket_name}, Region: {settings.AWS_REGION}")
            logger.info(f"Content-Type: {content_type}")

            # Upload file (public access controlled by bucket policy, not ACL)
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type
                }
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Upload successful: {url}")
            return url

        except ClientError as e:
            logger.error(f"S3 ClientError uploading {filename}: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading {filename} to S3: {str(e)}")
            return None

    def upload_content(
        self,
        content: bytes,
        filename: str,
        folder: str,
        content_type: str
    ) -> Optional[str]:
        """
        Upload content directly to S3 from bytes.

        Args:
            content: Content as bytes to upload
            folder: Folder path in S3 (e.g., 'chats', 'exports')
            filename: Filename to use in S3
            content_type: MIME type of the content

        Returns:
            S3 URL of the uploaded file or None if failed
        """
        try:
            s3_key = f"{folder}/{filename}"

            logger.info(f"Starting S3 content upload: {filename} -> {s3_key}")
            logger.info(f"Bucket: {self.bucket_name}, Content length: {len(content)}")

            # Upload content
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Upload successful: {url}")
            return url

        except ClientError as e:
            logger.error(f"S3 ClientError uploading content: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading content to S3: {str(e)}")
            return None

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for accessing a private S3 object.

        Args:
            s3_key: S3 object key
            expiration: Time in seconds for the presigned URL to remain valid

        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def generate_presigned_url_from_s3_url(self, s3_url: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL from a full S3 URL.

        Args:
            s3_url: Full S3 URL (e.g., https://bucket.s3.region.amazonaws.com/key)
            expiration: Time in seconds for the presigned URL to remain valid (default: 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        try:
            # Extract S3 key from URL
            # Format: https://bucket.s3.region.amazonaws.com/folder/file.ext
            parts = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")
            if len(parts) < 2:
                logger.error(f"Invalid S3 URL format: {s3_url}")
                return s3_url  # Return original URL as fallback

            s3_key = parts[1]
            return self.generate_presigned_url(s3_key, expiration)
        except Exception as e:
            logger.error(f"Error generating presigned URL from S3 URL: {e}")
            return s3_url  # Return original URL as fallback

    def delete_file(self, s3_url: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_url: Full S3 URL of the file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract S3 key from URL
            s3_key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except (ClientError, IndexError) as e:
            print(f"Error deleting file from S3: {e}")
            return False

    def get_file_size(self, s3_url: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            s3_url: Full S3 URL of the file

        Returns:
            File size in bytes or None if failed
        """
        try:
            s3_key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['ContentLength']
        except (ClientError, IndexError) as e:
            print(f"Error getting file size: {e}")
            return None


# Singleton instance
s3_service = S3Service()
