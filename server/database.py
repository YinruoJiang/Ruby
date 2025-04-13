import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

def get_db():
    """Get a database connection."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

def init_db():
    """Initialize the database with required tables."""
    try:
        conn = get_db()
        cur = conn.cursor()
        logger.info("Creating database tables...")
        
        # Drop existing tables if they exist
        cur.execute('DROP TABLE IF EXISTS images CASCADE')
        cur.execute('DROP TABLE IF EXISTS messages CASCADE')
        
        # Create images table
        cur.execute('''
            CREATE TABLE images (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                upload_time TIMESTAMP NOT NULL
            )
        ''')
        logger.info("Created images table")
        
        # Create messages table
        cur.execute('''
            CREATE TABLE messages (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Created messages table")
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def get_all_images():
    """Get all images from the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM images ORDER BY upload_time DESC')
        images = cur.fetchall()
        return [{"id": img[0], "filename": img[1], "upload_time": img[2].isoformat()} for img in images]
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

def save_image(filename, upload_time):
    """Save image metadata to the database."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO images (filename, upload_time) VALUES (%s, %s) RETURNING id',
            (filename, upload_time)
        )
        image_id = cur.fetchone()[0]
        conn.commit()
        return image_id
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
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