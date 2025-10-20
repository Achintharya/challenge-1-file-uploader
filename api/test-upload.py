"""
Test endpoint to verify S3 connection
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import boto3
from botocore.exceptions import ClientError

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test S3 connection and bucket access"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get environment variables
        AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        S3_BUCKET = os.environ.get('S3_BUCKET')
        
        response = {
            'environment': {
                'AWS_KEY_SET': bool(AWS_ACCESS_KEY_ID),
                'AWS_SECRET_SET': bool(AWS_SECRET_ACCESS_KEY),
                'S3_BUCKET': S3_BUCKET,
                'AWS_REGION': AWS_REGION
            }
        }
        
        # Try to connect to S3
        if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
            try:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                )
                
                # Try to check if bucket exists
                try:
                    s3.head_bucket(Bucket=S3_BUCKET)
                    response['s3_connection'] = 'SUCCESS'
                    response['bucket_exists'] = True
                    
                    # Try to list bucket location
                    try:
                        location = s3.get_bucket_location(Bucket=S3_BUCKET)
                        response['bucket_region'] = location['LocationConstraint'] or 'us-east-1'
                    except Exception as e:
                        response['bucket_region_error'] = str(e)
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '404':
                        response['s3_connection'] = 'BUCKET_NOT_FOUND'
                        response['bucket_exists'] = False
                    else:
                        response['s3_connection'] = f'ERROR: {error_code}'
                        response['error_details'] = str(e)
                        
            except Exception as e:
                response['s3_connection'] = 'FAILED'
                response['error'] = str(e)
                response['error_type'] = type(e).__name__
        else:
            response['s3_connection'] = 'MISSING_CREDENTIALS'
            
        self.wfile.write(json.dumps(response, indent=2).encode())
