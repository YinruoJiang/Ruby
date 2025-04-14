import os
import psycopg2
from dotenv import load_dotenv
import logging
import bcrypt

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Drop the table if it exists to ensure clean state
        cur.execute('DROP TABLE IF EXISTS users')
        
        # Create users table
        cur.execute('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create an index on the username column for faster queries
        cur.execute('CREATE INDEX idx_users_username ON users(username)')
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise

def create_user(username, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        cur.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id
        ''', (username, password_hash.decode('utf-8')))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise

def get_user_by_username(username):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, username, password_hash
            FROM users
            WHERE username = %s
        ''', (username,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'password_hash': user[2]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise

def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False 