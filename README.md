# Challenge 1: Cloud File Uploader (Vercel-Ready)

## Objective

Build a web application that allows users to upload files and saves them to AWS S3 cloud storage.

## Features

- Simple web interface for file uploads
- Serverless backend API using Vercel Functions
- AWS S3 cloud storage integration
- Returns public URL for uploaded files
- File size limit (10MB) and type validation
- Supports images (jpg, png, gif) and documents (pdf, txt)

## Project Structure

```
challenge-1-file-uploader/
├── api/                    # Vercel serverless functions
│   └── upload.py          # File upload handler
├── public/                # Static frontend files
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
└── README.md
```

## API Endpoint

### POST /api/upload

Upload a file to S3

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: File data

**Response:**

```json
{
  "success": true,
  "url": "https://bucket.s3.region.amazonaws.com/filename.jpg",
  "filename": "filename.jpg"
}
```

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Backend**: Python with Vercel Serverless Functions
- **Cloud Storage**: AWS S3
- **Deployment**: Vercel

## Security Considerations

- Never commit `.env` file with real credentials
- Use environment variables in Vercel Dashboard
- Implement rate limiting for production use
- Consider adding authentication for sensitive files

## Troubleshooting

### CORS Issues

The API already includes CORS headers. If you still face issues, check your S3 bucket CORS configuration.

### File Upload Fails

- Check AWS credentials in Vercel environment variables
- Verify S3 bucket exists and has proper permissions
- Ensure file size is under 10MB
- Check file type is allowed (jpg, png, gif, pdf, txt)

### Vercel Function Timeout

Default timeout is 10 seconds. For larger files, you may need to upgrade to Vercel Pro for longer timeouts.

## AI Tools Used

- GitHub Copilot for code generation
- ChatGPT for debugging and optimization

## License

MIT
