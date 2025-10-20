"""
Vercel Serverless Function for File Upload to AWS S3
"""

import os
import json
import boto3
import traceback
from werkzeug.utils import secure_filename

# AWS S3 Configuration from environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET')

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'}

# Log environment setup
print(f"[INFO] Environment setup:")
print(f"  AWS_REGION: {AWS_REGION}")
print(f"  S3_BUCKET: {S3_BUCKET}")
print(f"  AWS_ACCESS_KEY_ID exists: {bool(AWS_ACCESS_KEY_ID)}")
print(f"  AWS_SECRET_ACCESS_KEY exists: {bool(AWS_SECRET_ACCESS_KEY)}")

# Create S3 client
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    print("[INFO] S3 client created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create S3 client: {str(e)}")
    s3 = None


def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def handler(request):
    """Vercel serverless function handler"""
    
    print(f"[INFO] Request method: {request.method}")
    print(f"[INFO] Request headers: {dict(request.headers)}")
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        print("[INFO] Handling CORS preflight request")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    # Only allow POST requests
    if request.method != 'POST':
        print(f"[ERROR] Method not allowed: {request.method}")
        return {
            'statusCode': 405,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Check if S3 client is available
        if not s3:
            print("[ERROR] S3 client is not initialized")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'S3 client not initialized. Check AWS credentials.'})
            }
        
        # Check if bucket is configured
        if not S3_BUCKET:
            print("[ERROR] S3_BUCKET not configured")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'S3 bucket not configured'})
            }
        
        # Log files in request
        print(f"[INFO] Files in request: {list(request.files.keys())}")
        
        # Get file from request
        if 'file' not in request.files:
            print("[ERROR] No file provided in request")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'No file provided'})
            }
        
        file = request.files['file']
        print(f"[INFO] File received: {file.filename}")
        
        # Check if file is selected
        if file.filename == '':
            print("[ERROR] Empty filename")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'No file selected'})
            }
        
        # Check file type
        if not allowed_file(file.filename):
            print(f"[ERROR] File type not allowed: {file.filename}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'})
            }
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        print(f"[INFO] File size: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            print(f"[ERROR] File too large: {file_size} bytes")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': f'File too large. Max size is 10MB, got {file_size/1024/1024:.2f}MB'})
            }
        
        # Get safe filename
        filename = secure_filename(file.filename)
        print(f"[INFO] Secure filename: {filename}")
        
        # Upload to S3
        try:
            print(f"[INFO] Uploading to S3 bucket: {S3_BUCKET}")
            s3.upload_fileobj(
                file,
                S3_BUCKET,
                filename,
                ExtraArgs={'ACL': 'public-read'}
            )
            print(f"[SUCCESS] File uploaded successfully: {filename}")
        except Exception as s3_error:
            print(f"[ERROR] S3 upload failed: {str(s3_error)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': f'S3 upload failed: {str(s3_error)}',
                    'details': {
                        'bucket': S3_BUCKET,
                        'filename': filename,
                        'error_type': type(s3_error).__name__
                    }
                })
            }
        
        # Create public URL
        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        print(f"[SUCCESS] File URL: {file_url}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'url': file_url,
                'filename': filename,
                'size': file_size,
                'bucket': S3_BUCKET
            })
        }
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__,
                'details': 'Check server logs for more information'
            })
        }
