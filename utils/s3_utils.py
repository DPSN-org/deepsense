"""
S3 utilities for uploading JSON data and files.
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
            'source': 'langgraph-utils'
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


def upload_file_to_s3(
    file_path: str,
    bucket_name: str,
    key: Optional[str] = None,
    region_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a file to S3 bucket.
    
    Args:
        file_path: Local file path to upload
        bucket_name: S3 bucket name
        key: S3 object key (if None, uses filename from file_path)
        region_name: AWS region (defaults to environment variable or 'us-east-1')
        aws_access_key_id: AWS access key (defaults to environment variable)
        aws_secret_access_key: AWS secret key (defaults to environment variable)
        content_type: Content type for the S3 object (auto-detected if None)
        metadata: Optional metadata to attach to the S3 object
        
    Returns:
        Dictionary with upload result information
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "error_type": "FileNotFoundError"
            }
        
        # Use filename as key if not provided
        if key is None:
            key = os.path.basename(file_path)
        
        # Auto-detect content type if not provided
        if content_type is None:
            if file_path.endswith('.json'):
                content_type = 'application/json'
            elif file_path.endswith('.txt'):
                content_type = 'text/plain'
            elif file_path.endswith('.csv'):
                content_type = 'text/csv'
            else:
                content_type = 'application/octet-stream'
        
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
            'original_filename': os.path.basename(file_path),
            'source': 'langgraph-utils'
        }
        if metadata:
            upload_metadata.update(metadata)
        
        # Upload file to S3 with public read access
        with open(file_path, 'rb') as file:
            try:
                response = s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=file,
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
                        Body=file,
                        ContentType=content_type,
                        Metadata=upload_metadata
                    )
                else:
                    raise
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
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
            "size_bytes": file_size,
            "upload_timestamp": upload_metadata['upload_timestamp'],
            "original_file": file_path,
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


def generate_s3_key(prefix: str = "data", filename: Optional[str] = None, timestamp: bool = True) -> str:
    """
    Generate a unique S3 key for uploading files.
    
    Args:
        prefix: Directory prefix for the S3 key
        filename: Custom filename (if None, generates one)
        timestamp: Whether to include timestamp in the key
        
    Returns:
        Generated S3 key
    """
    if filename is None:
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"upload_{timestamp_str}.json"
    elif timestamp:
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp_str}{ext}"
    
    return f"{prefix}/{filename}"


# Example usage functions
def upload_test_results_to_s3(
    test_results: Dict[str, Any],
    bucket_name: str,
    test_name: str = "test_results"
) -> Dict[str, Any]:
    """
    Upload test results to S3 with automatic key generation.
    
    Args:
        test_results: Test results dictionary
        bucket_name: S3 bucket name
        test_name: Name for the test (used in S3 key)
        
    Returns:
        Upload result
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f"test-results/{test_name}_{timestamp}.json"
    
    return upload_json_to_s3(
        data=test_results,
        bucket_name=bucket_name,
        key=key,
        metadata={
            "test_name": test_name,
            "upload_type": "test_results"
        }
    )


def upload_schema_results_to_s3(
    schema_results: Dict[str, Any],
    bucket_name: str,
    data_source: str = "unknown"
) -> Dict[str, Any]:
    """
    Upload schema discovery results to S3.
    
    Args:
        schema_results: Schema discovery results
        bucket_name: S3 bucket name
        data_source: Source of the data (e.g., 'helius', 'api', etc.)
        
    Returns:
        Upload result
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f"schemas/{data_source}_schema_{timestamp}.json"
    
    return upload_json_to_s3(
        data=schema_results,
        bucket_name=bucket_name,
        key=key,
        metadata={
            "data_source": data_source,
            "upload_type": "schema_discovery"
        }
    ) 