"""
S3 utilities for uploading JSON data.
"""

import json
import os
import boto3
from typing import Dict, Any, Union, Optional
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


def upload_json_to_s3(
    data: Union[Dict[str, Any], str],
    bucket_name: str,
    key: str,
    region_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    content_type: str = "application/json",
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload JSON data to S3 bucket.
    
    Args:
        data: JSON data as dictionary or JSON string
        bucket_name: S3 bucket name
        key: S3 object key (file path in bucket)
        region_name: AWS region (defaults to environment variable or 'us-east-1')
        aws_access_key_id: AWS access key (defaults to environment variable)
        aws_secret_access_key: AWS secret key (defaults to environment variable)
        content_type: Content type for the S3 object
        metadata: Optional metadata to attach to the S3 object
        
    Returns:
        Dictionary with upload result information
        
    Raises:
        NoCredentialsError: If AWS credentials are not found
        ClientError: If S3 upload fails
    """
    try:
        # Convert data to JSON string if it's a dictionary
        if isinstance(data, dict):
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
        elif isinstance(data, str):
            json_data = data
        else:
            raise ValueError("Data must be a dictionary or JSON string")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=region_name or os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Prepare metadata
        upload_metadata = {
            'upload_timestamp': datetime.now().isoformat(),
            'content_type': 'application/json',
            'source': 'deepsense-framework'
        }
        if metadata:
            upload_metadata.update(metadata)
        
        # Upload to S3 with public read access
        try:
            response = s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType=content_type,
                Metadata=upload_metadata,
                ACL='public-read'  # Make the object publicly readable
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessControlListNotSupported':
                # Bucket doesn't support ACLs, upload without ACL
                print(f"⚠️  Bucket {bucket_name} doesn't support ACLs, uploading without public-read")
                response = s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=json_data.encode('utf-8'),
                    ContentType=content_type,
                    Metadata=upload_metadata
                )
            else:
                raise
        
        # Generate S3 URL
        s3_url = f"s3://{bucket_name}/{key}"
        https_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
        
        return {
            "success": True,
            "bucket": bucket_name,
            "key": key,
            "s3_url": s3_url,
            "https_url": https_url,
            "etag": response.get('ETag', '').strip('"'),
            "size_bytes": len(json_data.encode('utf-8')),
            "upload_timestamp": upload_metadata['upload_timestamp'],
            "response": response
        }
        
    except NoCredentialsError:
        return {
            "success": False,
            "error": "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or pass them as parameters.",
            "error_type": "NoCredentialsError"
        }
    except ClientError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "ClientError",
            "error_code": e.response['Error']['Code'] if 'Error' in e.response else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

