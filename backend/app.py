"""
Simple File Uploader Backend with AWS S3
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt'}

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET')

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Create temp folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    """Simple health check"""
    return jsonify({'status': 'running'}), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload file to AWS S3"""
    
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file type
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Max size is 10MB'}), 400
    
    try:
        # Get safe filename
        filename = secure_filename(file.filename)
        
        # Save file temporarily
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        # Upload to S3
        s3.upload_file(
            temp_path,
            S3_BUCKET,
            filename,
            ExtraArgs={'ACL': 'public-read'}  # Make file public
        )
        
        # Create public URL
        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        
        # Delete temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'url': file_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000)
