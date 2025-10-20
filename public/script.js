// Simple File Upload Script
// Configuration
const BACKEND_URL = '/api'; // Vercel API endpoint
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes

// Global variable to store selected file
let selectedFile = null;

// Get all HTML elements we need
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const uploadBtn = document.getElementById('uploadBtn');
const cancelBtn = document.getElementById('cancelBtn');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const result = document.getElementById('result');
const error = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const fileUrl = document.getElementById('fileUrl');

// When user selects a file
fileInput.addEventListener('change', function() {
    const file = fileInput.files[0];
    if (file) {
        checkFile(file);
    }
});

// Check if file is valid
function checkFile(file) {
    // Check file size (10MB limit)
    if (file.size > MAX_FILE_SIZE) {
        showError('File is too large! Maximum size is 10MB.');
        return;
    }
    
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type! Only JPG, PNG, GIF, PDF, and TXT files are allowed.');
        return;
    }
    
    // File is valid, save it
    selectedFile = file;
    showFilePreview(file);
}

// Show file preview
function showFilePreview(file) {
    // Display file name
    fileName.textContent = file.name;
    
    // Display file size in KB or MB
    let sizeText = '';
    if (file.size < 1024 * 1024) {
        sizeText = Math.round(file.size / 1024) + ' KB';
    } else {
        sizeText = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    }
    fileSize.textContent = sizeText;
    
    // Show preview, hide upload area
    uploadArea.style.display = 'none';
    filePreview.style.display = 'block';
}

// Upload button clicked
uploadBtn.addEventListener('click', function() {
    if (selectedFile) {
        uploadFile();
    }
});

// Cancel button clicked
cancelBtn.addEventListener('click', resetUploader);

// Upload file to server
function uploadFile() {
    // Create form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Hide preview, show progress bar
    filePreview.style.display = 'none';
    progressBar.style.display = 'block';
    
    // Use fetch API to send file
    fetch(BACKEND_URL + '/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Upload failed');
        }
    })
    .then(data => {
        // Upload successful
        showSuccess(data.url);
    })
    .catch(err => {
        // Upload failed
        showError('Upload failed. Please try again.');
        console.error('Upload error:', err);
    });
    
    // Simulate progress (since fetch doesn't support progress)
    simulateProgress();
}

// Simulate upload progress
function simulateProgress() {
    let progress = 0;
    const interval = setInterval(function() {
        progress += 10;
        progressFill.style.width = progress + '%';
        
        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 200);
}

// Show success message
function showSuccess(url) {
    // Hide all other sections
    hideAll();
    
    // Show success message
    fileUrl.value = url || 'File uploaded successfully';
    result.style.display = 'block';
    
    // Complete progress bar
    progressFill.style.width = '100%';
}

// Show error message
function showError(message) {
    // Hide all other sections
    hideAll();
    
    // Show error message
    errorMessage.textContent = message;
    error.style.display = 'block';
}

// Copy URL to clipboard
function copyUrl() {
    // Select the URL text
    fileUrl.select();
    
    // Copy to clipboard
    document.execCommand('copy');
    
    // Show feedback
    const button = event.target;
    button.textContent = 'Copied!';
    
    // Reset button text after 2 seconds
    setTimeout(function() {
        button.textContent = 'Copy URL';
    }, 2000);
}

// Reset everything to start over
function resetUploader() {
    // Clear selected file
    selectedFile = null;
    fileInput.value = '';
    
    // Reset progress bar
    progressFill.style.width = '0%';
    
    // Hide all sections
    hideAll();
    
    // Show upload area
    uploadArea.style.display = 'block';
}

// Hide all sections
function hideAll() {
    uploadArea.style.display = 'none';
    filePreview.style.display = 'none';
    progressBar.style.display = 'none';
    result.style.display = 'none';
    error.style.display = 'none';
}

// Make functions available to HTML onclick attributes
window.copyUrl = copyUrl;
window.resetUploader = resetUploader;
