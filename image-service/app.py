from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import os
import logging
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import init_db, save_image_metadata, get_user_images, delete_image

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")

app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize database with error handling
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    # Continue running the app even if database initialization fails
    # This allows us to handle the error in the routes

# Configure CORS with more permissive settings for development
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200
            
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split()[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST', 'OPTIONS'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file to disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Save metadata to database
        try:
            save_image_metadata(
                filename=unique_filename,
                original_filename=filename,
                owner=current_user,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type
            )
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': unique_filename,
                'original_filename': filename
            })
        except Exception as e:
            logger.error(f"Error saving image metadata: {str(e)}")
            # Clean up the file if database save fails
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'message': 'Error saving image metadata'}), 500
    
    return jsonify({'message': 'File type not allowed'}), 400

@app.route('/images', methods=['GET', 'OPTIONS'])
@token_required
def get_images(current_user):
    try:
        logger.info(f"Fetching images for user: {current_user}")
        images = get_user_images(current_user)
        logger.info(f"Found {len(images)} images for user {current_user}")
        return jsonify({'images': images})
    except Exception as e:
        logger.error(f"Error getting images for user {current_user}: {str(e)}")
        return jsonify({
            'message': 'Error retrieving images',
            'error': str(e)
        }), 500

@app.route('/images/<filename>', methods=['DELETE', 'OPTIONS'])
@token_required
def delete_image_route(current_user, filename):
    try:
        # Delete from database first
        if delete_image(filename, current_user):
            # If database delete successful, delete the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'message': 'Image deleted successfully'})
        return jsonify({'message': 'Image not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        return jsonify({'message': 'Error deleting image'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3003, debug=True) 