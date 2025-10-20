"""
Vercel Serverless Function for File Upload to AWS S3
Simplified handler for Vercel
"""

import os
import json
import traceback

def handler(request, response):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response.status_code = 200
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ""
    
    # Set CORS headers for all responses
    response.headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    # Only allow POST requests
    if request.method != 'POST':
        response.status_code = 405
        return json.dumps({'error': 'Method not allowed'})
    
    try:
        import boto3
        from werkzeug.utils import secure_filename
        
        # Get environment variables
        AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        S3_BUCKET = os.environ.get('S3_BUCKET')
        
        # Check if environment variables are set
        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
            missing = []
            if not AWS_ACCESS_KEY_ID:
                missing.append('AWS_ACCESS_KEY_ID')
            if not AWS_SECRET_ACCESS_KEY:
                missing.append('AWS_SECRET_ACCESS_KEY')
            if not S3_BUCKET:
                missing.append('S3_BUCKET')
            
            response.status_code = 500
            return json.dumps({
                'error': 'Missing environment variables',
                'missing': missing,
                'hint': 'Please set these in Vercel Dashboard > Settings > Environment Variables'
            })
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Check if file exists in request
        if not hasattr(request, 'files') or 'file' not in request.files:
            response.status_code = 400
            return json.dumps({'error': 'No file provided in request'})
        
        file = request.files['file']
        
        # Validate file
        if not file or file.filename == '':
            response.status_code = 400
            return json.dumps({'error': 'No file selected'})
        
        # Check file extension
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'}
        filename = secure_filename(file.filename)
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            response.status_code = 400
            return json.dumps({
                'error': 'File type not allowed',
                'allowed': list(ALLOWED_EXTENSIONS)
            })
        
        # Check file size (10MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            response.status_code = 400
            return json.dumps({
                'error': 'File too large',
                'max_size': '10MB',
                'file_size': f'{file_size / (1024*1024):.2f}MB'
            })
        
        # Upload to S3
        try:
            s3.upload_fileobj(
                file,
                S3_BUCKET,
                filename,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            # Generate public URL
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
            
            response.status_code = 200
            return json.dumps({
                'success': True,
                'url': file_url,
                'filename': filename
            })
            
        except Exception as s3_error:
            response.status_code = 500
            return json.dumps({
                'error': 'S3 upload failed',
                'message': str(s3_error),
                'bucket': S3_BUCKET,
                'region': AWS_REGION
            })
            
    except ImportError as e:
        response.status_code = 500
        return json.dumps({
            'error': 'Missing dependencies',
            'message': str(e),
            'hint': 'Check requirements.txt includes boto3 and werkzeug'
        })
    except Exception as e:
        response.status_code = 500
        return json.dumps({
            'error': 'Unexpected error',
            'message': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        })
