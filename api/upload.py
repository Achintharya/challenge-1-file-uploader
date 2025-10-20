"""
Vercel Serverless Function for File Upload to AWS S3
Fixed multipart handling
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import boto3
from botocore.exceptions import ClientError
import cgi
import io

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
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Get environment variables
            AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
            AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
            AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
            S3_BUCKET = os.environ.get('S3_BUCKET')
            
            # Parse the multipart form data
            content_type = self.headers.get('Content-Type')
            
            # Create a cgi.FieldStorage object to parse multipart data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
            )
            
            # Get the uploaded file
            if 'file' not in form:
                error_response = {'error': 'No file in request', 'success': False}
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            file_item = form['file']
            
            # Check if file is present
            if not file_item.filename:
                error_response = {'error': 'No file selected', 'success': False}
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # Get file details
            filename = file_item.filename
            file_data = file_item.file.read()
            
            # Validate file extension
            ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'}
            if '.' in filename:
                ext = filename.rsplit('.', 1)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    error_response = {
                        'error': f'File type .{ext} not allowed',
                        'allowed': list(ALLOWED_EXTENSIONS),
                        'success': False
                    }
                    self.wfile.write(json.dumps(error_response).encode())
                    return
            
            # Check file size (10MB max)
            if len(file_data) > 10 * 1024 * 1024:
                error_response = {
                    'error': 'File too large',
                    'max_size': '10MB',
                    'file_size': f'{len(file_data) / (1024*1024):.2f}MB',
                    'success': False
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # Create S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            
            # Make filename safe and unique
            import time
            safe_filename = f"{int(time.time())}_{filename.replace(' ', '_')}"
            
            # Upload to S3
            try:
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=safe_filename,
                    Body=file_data,
                    ACL='public-read',
                    ContentType=file_item.type if hasattr(file_item, 'type') else 'application/octet-stream'
                )
                
                # Generate public URL
                file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{safe_filename}"
                
                # Success response
                response = {
                    'success': True,
                    'url': file_url,
                    'filename': safe_filename,
                    'original_name': filename,
                    'size': len(file_data)
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            except ClientError as e:
                error_response = {
                    'error': 'S3 upload failed',
                    'details': str(e),
                    'success': False
                }
                self.wfile.write(json.dumps(error_response).encode())
                
        except Exception as e:
            error_response = {
                'error': 'Server error',
                'message': str(e),
                'type': type(e).__name__,
                'success': False
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """Handle GET request for testing"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'Upload API is running',
            'method': 'Use POST with multipart/form-data to upload files',
            'endpoint': '/api/upload',
            'test_endpoint': '/api/test-upload',
            'allowed_types': ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'],
            'max_size': '10MB'
        }
        
        self.wfile.write(json.dumps(response).encode())
