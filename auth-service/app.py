from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import os
from functools import wraps
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"]
    }
})

# Mock user database (replace with actual database in production)
USERS = {
    "test": {
        "password": "test123",
        "id": 1
    }
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401

    user = USERS.get(auth['username'])
    if not user or user['password'] != auth['password']:
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user': auth['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return jsonify({'token': token})

@app.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    return jsonify({'message': 'Token is valid', 'user': current_user})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=True) 