import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import uuid
from config.settings import settings
from core.logging import logger
import aiofiles
import os


class S3Service:
    """Service for AWS S3 file operations"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Error creating bucket: {create_error}")
            else:
                logger.error(f"Error checking bucket: {e}")
    
    def generate_s3_key(self, agent_id: str, filename: str) -> str:
        """Generate S3 key for file"""
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        return f"agents/{agent_id}/documents/{file_uuid}{file_extension}"
    
    def generate_presigned_upload_url(
        self,
        s3_key: str,
        file_type: str,
        expiration: int = None
    ) -> Dict[str, Any]:
        """Generate presigned URL for direct file upload (PUT method)
        
        Returns:
            Dictionary with upload URL and S3 key
        """
        try:
            expiration = expiration or settings.AWS_S3_PRESIGNED_URL_EXPIRY
            
            # Generate presigned URL for PUT
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': file_type
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned upload URL for: {s3_key}")
            
            return {
                'upload_url': url,
                's3_key': s3_key,
                'fields': {}  # Empty for compatibility with response model
            }
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def generate_presigned_download_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file download"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise
    
    async def upload_file(
        self,
        file_path: str,
        s3_key: str,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file directly to S3
        
        Returns:
            S3 URL of uploaded file
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            
            # Return S3 URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            return url
            
        except ClientError as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(
        self,
        s3_key: str,
        local_path: str
    ):
        """Download file from S3 to local path"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Downloaded file from S3: {s3_key} -> {local_path}")
        except ClientError as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def delete_file(self, s3_key: str):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted file from S3: {s3_key}")
        except ClientError as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    async def list_files(self, prefix: str) -> list:
        """List files with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            
            return files
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def get_file_url(self, s3_key: str) -> str:
        """Get public URL for S3 file"""
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


# Singleton instance
s3_service = S3Service()
