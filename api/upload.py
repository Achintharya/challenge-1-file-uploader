"""
Vercel Serverless Function for File Upload to AWS S3
Full implementation with S3 upload
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import cgi
import io
import boto3
from botocore.exceptions import ClientError

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return

    def do_POST(self):
        """Handle file upload POST request"""
        try:
            # Get environment variables
            AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
            AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
            AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
            S3_BUCKET = os.environ.get('S3_BUCKET')
            
            # Check environment variables
            if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
                self.send_error_response(500, 'Missing environment variables', {
                    'missing': [
                        k for k in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET']
                        if not os.environ.get(k)
                    ]
                })
                return
            
            # Parse multipart form data
            content_type = self.headers.get('Content-Type')
            if not content_type or 'multipart/form-data' not in content_type:
                self.send_error_response(400, 'Content-Type must be multipart/form-data')
                return
            
            # Parse the form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )
            
            # Get the file
            if 'file' not in form:
                self.send_error_response(400, 'No file provided')
                return
            
            file_item = form['file']
            
            # Check if file was uploaded
            if not file_item.filename:
                self.send_error_response(400, 'No file selected')
                return
            
            # Get filename and validate extension
            filename = file_item.filename
            ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'}
            
            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                self.send_error_response(400, f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}')
                return
            
            # Read file data
            file_data = file_item.file.read()
            
            # Check file size (10MB max)
            if len(file_data) > 10 * 1024 * 1024:
                self.send_error_response(400, f'File too large. Max 10MB, got {len(file_data) / (1024*1024):.2f}MB')
                return
            
            # Create S3 client
            try:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                )
            except Exception as e:
                self.send_error_response(500, f'Failed to create S3 client: {str(e)}')
                return
            
            # Upload to S3
            try:
                # Use a simple filename (you might want to add timestamp or UUID for uniqueness)
                safe_filename = filename.replace(' ', '_')
                
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=safe_filename,
                    Body=file_data,
                    ACL='public-read',
                    ContentType=file_item.type or 'application/octet-stream'
                )
                
                # Generate public URL
                file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{safe_filename}"
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'success': True,
                    'url': file_url,
                    'filename': safe_filename,
                    'size': len(file_data),
                    'bucket': S3_BUCKET
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                self.send_error_response(500, f'S3 upload failed: {error_code}', {
                    'error_code': error_code,
                    'bucket': S3_BUCKET,
                    'region': AWS_REGION
                })
            except Exception as e:
                self.send_error_response(500, f'Upload error: {str(e)}')
                
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')
    
    def send_error_response(self, status_code, message, details=None):
        """Helper to send error responses"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            'error': message,
            'success': False
        }
        
        if details:
            error_response['details'] = details
        
        self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """Handle GET request for testing"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'API is running',
            'method': 'Use POST with multipart/form-data to upload files',
            'endpoint': '/api/upload',
            'environment': {
                'AWS_KEY_SET': bool(os.environ.get('AWS_ACCESS_KEY_ID')),
                'AWS_SECRET_SET': bool(os.environ.get('AWS_SECRET_ACCESS_KEY')),
                'S3_BUCKET_SET': bool(os.environ.get('S3_BUCKET')),
                'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1')
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
