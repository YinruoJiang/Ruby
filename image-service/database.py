import os
import psycopg2
from dotenv import load_dotenv
import logging

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
        cur.execute('DROP TABLE IF EXISTS images')
        
        # Create images table
        cur.execute('''
            CREATE TABLE images (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                owner VARCHAR(255) NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size BIGINT NOT NULL,
                mime_type VARCHAR(100) NOT NULL
            )
        ''')
        
        # Create an index on the owner column for faster queries
        cur.execute('CREATE INDEX idx_images_owner ON images(owner)')
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise

def save_image_metadata(filename, original_filename, owner, file_size, mime_type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO images (filename, original_filename, owner, file_size, mime_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (filename, original_filename, owner, file_size, mime_type))
        
        image_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return image_id
    except Exception as e:
        logger.error(f"Error saving image metadata: {str(e)}")
        raise

def get_user_images(owner):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verify the table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'images'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            logger.info("Images table does not exist, creating it...")
            init_db()
            return []  # Return empty list for new table
        
        cur.execute('''
            SELECT filename, original_filename, upload_date, file_size, mime_type
            FROM images
            WHERE owner = %s
            ORDER BY upload_date DESC
        ''', (owner,))
        
        images = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            'filename': img[0],
            'original_filename': img[1],
            'upload_date': img[2].isoformat() if img[2] else None,
            'file_size': img[3],
            'mime_type': img[4]
        } for img in images]
    except Exception as e:
        logger.error(f"Error getting user images: {str(e)}")
        logger.error(f"Database URL: {DATABASE_URL}")
        if 'conn' in locals():
            conn.rollback()
        raise

def delete_image(filename, owner):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            DELETE FROM images
            WHERE filename = %s AND owner = %s
            RETURNING id
        ''', (filename, owner))
        
        deleted = cur.fetchone() is not None
        conn.commit()
        cur.close()
        conn.close()
        return deleted
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise 