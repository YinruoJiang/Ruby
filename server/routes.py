from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import logging
from .database import get_all_images, save_image, create_message, get_all_messages
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Create a blueprint for the API
api = Blueprint('api', __name__)

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_db_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function

# Image routes
@api.route('/images')
def get_images():
    try:
        logger.info("GET /api/images request received")
        images = get_all_images()
        logger.info(f"Returning {len(images)} images")
        return jsonify(images)
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        return jsonify({'error': f'Error fetching images: {str(e)}'}), 500

@api.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        logger.info("POST /api/upload-image request received")
        
        if 'image' not in request.files:
            logger.error("No image file in request")
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            logger.error("Empty filename in request")
            return jsonify({'error': 'No selected file'}), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            try:
                logger.info(f"Saving file to: {filepath}")
                file.save(filepath)
                
                # Save metadata to database
                logger.info("Saving metadata to database")
                current_time = datetime.now()
                image_id = save_image(filename, current_time)
                
                logger.info("Upload completed successfully")
                return jsonify({
                    'success': True,
                    'message': 'Image uploaded successfully',
                    'filename': filename,
                    'id': image_id
                }), 200
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                return jsonify({'error': f'Error saving file: {str(e)}'}), 500
        else:
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'File type not allowed. Please upload PNG, JPG, or GIF files.'}), 400
    except Exception as e:
        logger.error(f"Error in upload_image: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Message routes
@api.route('/messages', methods=['POST'])
@handle_db_errors
def create_message_route():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
        
    content = data['content']
    if not content.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    try:
        message = create_message(content)
        return jsonify(message), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/messages', methods=['GET'])
@handle_db_errors
def get_messages_route():
    try:
        messages = get_all_messages()
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 