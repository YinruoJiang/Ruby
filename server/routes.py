from flask import Blueprint, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import logging
from .database import get_all_images, save_image, create_user, get_user_by_username, verify_password, get_images_by_user_id
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Auth routes
@api.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"Registration attempt for user: {username}")
        
        if not username or not password:
            logger.warning("Registration failed: Missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400
            
        # Check if user already exists
        existing_user = get_user_by_username(username)
        if existing_user:
            logger.warning(f"Registration failed: User {username} already exists")
            return jsonify({'error': 'Username already exists'}), 400
            
        logger.info(f"Creating new user: {username}")
        # Create new user
        user_id = create_user(username, password)
        logger.info(f"User created successfully with ID: {user_id}")
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        
        logger.info(f"Registration successful for user: {username}")
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user_id,
                'username': username
            }
        }), 201
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"Login attempt for user: {username}")
        
        if not username or not password:
            logger.warning("Login failed: Missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400
            
        # Get user from database
        user = get_user_by_username(username)
        if not user:
            logger.warning(f"Login failed: User {username} not found")
            return jsonify({'error': 'Invalid username or password'}), 401
            
        logger.info(f"User found: {user['username']}")
        logger.info("Verifying password...")
            
        # Verify password
        if not verify_password(password, user['password_hash']):
            logger.warning(f"Login failed: Invalid password for user {username}")
            return jsonify({'error': 'Invalid username or password'}), 401
            
        logger.info("Password verified successfully")
            
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        logger.info(f"Login successful for user {username}")
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        })
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@api.route('/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username']
            }
        })
    return jsonify({'authenticated': False})

# Image routes
@api.route('/images')
@login_required
def get_images():
    try:
        logger.info("GET /api/images request received")
        user_id = session.get('user_id')
        logger.info(f"Fetching images for user ID: {user_id}")
        images = get_images_by_user_id(user_id)
        logger.info(f"Returning {len(images)} images")
        return jsonify(images)
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        return jsonify({'error': f'Error fetching images: {str(e)}'}), 500

@api.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    try:
        logger.info("POST /api/upload-image request received")
        logger.info(f"Session user_id: {session.get('user_id')}")
        
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
                
                # Verify file was saved
                if not os.path.exists(filepath):
                    logger.error(f"File was not saved to {filepath}")
                    return jsonify({'error': 'Failed to save file'}), 500
                
                logger.info("File saved successfully")
                
                # Save metadata to database
                logger.info("Saving metadata to database")
                current_time = datetime.now()
                image_id = save_image(filename, current_time, session['user_id'])
                
                logger.info(f"Upload completed successfully. Image ID: {image_id}, Filename: {filename}")
                return jsonify({
                    'success': True,
                    'message': 'Image uploaded successfully',
                    'filename': filename,
                    'id': image_id,
                    'url': f"/uploads/{filename}"  # Add the URL to the response
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