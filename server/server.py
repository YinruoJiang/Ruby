from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Get the absolute path to the uploads directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__, static_url_path='', static_folder=UPLOAD_FOLDER)
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:3001", "http://localhost:3002"]},
    r"/uploads/*": {"origins": ["http://localhost:3001", "http://localhost:3002"]}
})

# Import and register the blueprint after app creation
from .routes import api
app.register_blueprint(api, url_prefix='/api')

# Root route
@app.route('/')
def index():
    logger.info("Root route accessed")
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'public'), 'index.html')

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'public'), 'favicon.ico')

# Initialize the database
from .database import init_db
init_db()

if __name__ == '__main__':
    logger.info("Starting server on port 3001")
    app.run(host='0.0.0.0', port=3001, debug=True) 