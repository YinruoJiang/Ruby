import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import logging
import bcrypt

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

def get_db():
    """Get a database connection."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

def check_database_state():
    """Check the current state of the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check users table
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        logger.info(f"Number of users in database: {user_count}")
        
        # List all users
        cur.execute("SELECT id, username FROM users")
        users = cur.fetchall()
        logger.info("Current users in database:")
        for user in users:
            logger.info(f"User ID: {user[0]}, Username: {user[1]}")
            
        return True
    except Exception as e:
        logger.error(f"Error checking database state: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def init_db():
    """Initialize the database with required tables."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info("Checking database tables...")
        
        # Create users table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Users table checked/created")
        
        # Create images table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP NOT NULL,
                user_id INTEGER REFERENCES users(id)
            )
        ''')
        logger.info("Images table checked/created")
        
        conn.commit()
        logger.info("Database initialization completed")
        
        # Check database state
        check_database_state()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def create_user(username, password):
    """Create a new user in the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        logger.info(f"Creating new user: {username}")
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        logger.debug(f"Generated password hash: {password_hash.decode('utf-8')}")
        
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, password_hash.decode('utf-8'))
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"User created successfully with ID: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    """Get a user by username."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "password_hash": user[2]
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_password(password, password_hash):
    """Verify a password against its hash."""
    try:
        logger.info("Starting password verification")
        logger.debug(f"Password hash from DB: {password_hash}")
        result = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        logger.info(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in password verification: {str(e)}")
        raise

def get_all_images():
    """Get all images from the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info("Fetching all images from database")
        
        cur.execute('SELECT * FROM images ORDER BY upload_time DESC')
        images = cur.fetchall()
        logger.info(f"Found {len(images)} images in database")
        
        result = [{"id": img[0], "filename": img[1], "upload_time": img[2].isoformat()} for img in images]
        logger.info("Successfully formatted image data")
        return result
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def save_image(filename, upload_time, user_id=None):
    """Save image metadata to the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info(f"Saving image metadata - Filename: {filename}, User ID: {user_id}")
        
        # If user_id is None, we'll use NULL in the database
        if user_id is None:
            logger.info("No user_id provided, saving image without user association")
            cur.execute(
                'INSERT INTO images (filename, upload_time) VALUES (%s, %s) RETURNING id',
                (filename, upload_time)
            )
        else:
            logger.info(f"Saving image with user_id: {user_id}")
            cur.execute(
                'INSERT INTO images (filename, upload_time, user_id) VALUES (%s, %s, %s) RETURNING id',
                (filename, upload_time, user_id)
            )
        
        image_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Image saved successfully with ID: {image_id}")
        return image_id
    except Exception as e:
        logger.error(f"Error saving image metadata: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def create_message(content):
    """Create a new message in the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (content) VALUES (%s) RETURNING id, content, created_at",
            (content,)
        )
        message = cur.fetchone()
        conn.commit()
        return {
            "id": message[0],
            "content": message[1],
            "created_at": message[2].isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_all_messages():
    """Get all messages from the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, content, created_at FROM messages ORDER BY created_at DESC")
        messages = cur.fetchall()
        return [{
            "id": msg[0],
            "content": msg[1],
            "created_at": msg[2].isoformat()
        } for msg in messages]
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_image_by_id(image_id):
    """Get a specific image by its ID."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info(f"Fetching image with ID: {image_id}")
        
        cur.execute('SELECT * FROM images WHERE id = %s', (image_id,))
        image = cur.fetchone()
        
        if image:
            logger.info(f"Found image with ID: {image_id}")
            return {"id": image[0], "filename": image[1], "upload_time": image[2].isoformat()}
        else:
            logger.warning(f"No image found with ID: {image_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching image with ID {image_id}: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_images_by_user_id(user_id):
    """Get all images for a specific user."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info(f"Fetching images for user ID: {user_id}")
        
        cur.execute('SELECT * FROM images WHERE user_id = %s ORDER BY upload_time DESC', (user_id,))
        images = cur.fetchall()
        logger.info(f"Found {len(images)} images for user {user_id}")
        
        result = [{"id": img[0], "filename": img[1], "upload_time": img[2].isoformat()} for img in images]
        logger.info("Successfully formatted image data")
        return result
    except Exception as e:
        logger.error(f"Error fetching images for user {user_id}: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close() 