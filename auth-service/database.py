import os
import psycopg2
from dotenv import load_dotenv
import logging
import bcrypt

# Configure logging
logger = logging.getLogger(__name__)

# Database connection string
DATABASE_URL = "postgresql://neondb_owner:npg_OXIi4xP9yelg@ep-yellow-waterfall-a5rllbr2-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db():
    """Get a database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def init_db():
    """Initialize the database with required tables."""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Create users table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def create_user(username, password):
    """Create a new user with hashed password."""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Insert new user
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, password_hash.decode('utf-8'))
        )
        
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        logger.error(f"Username {username} already exists")
        raise ValueError("Username already exists")
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    """Get user by username."""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,)
        )
        
        user = cur.fetchone()
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
    finally:
        cur.close()
        conn.close()

def verify_password(password, password_hash):
    """Verify password against stored hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        raise 