"""
Vercel Serverless Function for File Upload to AWS S3
"""

from http.server import BaseHTTPRequestHandler
import json
import os

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
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        try:
            # Check environment variables first
            AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
            AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
            AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
            S3_BUCKET = os.environ.get('S3_BUCKET')
            
            # If missing environment variables, return helpful error
            if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
                missing = []
                if not AWS_ACCESS_KEY_ID:
                    missing.append('AWS_ACCESS_KEY_ID')
                if not AWS_SECRET_ACCESS_KEY:
                    missing.append('AWS_SECRET_ACCESS_KEY')
                if not S3_BUCKET:
                    missing.append('S3_BUCKET')
                
                error_response = {
                    'error': 'Missing environment variables',
                    'missing': missing,
                    'hint': 'Please add these in Vercel Dashboard > Settings > Environment Variables'
                }
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # For now, return a test response to verify the function works
            response = {
                'success': True,
                'message': 'Function is working! Environment variables are set.',
                'config': {
                    'bucket': S3_BUCKET,
                    'region': AWS_REGION,
                    'aws_key_exists': bool(AWS_ACCESS_KEY_ID)
                }
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            error_response = {
                'error': 'Function error',
                'message': str(e),
                'type': type(e).__name__
            }
            self.wfile.write(json.dumps(error_response).encode())
            
    def do_GET(self):
        """Handle GET request for testing"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'API is running',
            'method': 'Use POST to upload files',
            'endpoint': '/api/upload'
        }
        
        self.wfile.write(json.dumps(response).encode())
