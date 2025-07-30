from flask import Flask, request, jsonify
from flask_cors import CORS # To handle Cross-Origin Resource Sharing
import psycopg2 # For PostgreSQL
import os
from datetime import datetime

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Database connection details from environment variables
# These will be set by Terraform/Jenkins for deployment,
# but provide defaults for local testing.
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'inkdrop_db') # Changed database name
DB_USER = os.environ.get('DB_USER', 'inkdrop') # Changed user
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Suman1508') # Changed password

def get_db_connection():
    """Establishes and returns a PostgreSQL database connection."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10 # Add a timeout for connection
        )
        print(f"✅ Successfully connected to database: {DB_NAME} on {DB_HOST}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        # Re-raise the exception or handle gracefully
        raise

# Initialize database schema on startup
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                author_name VARCHAR(255) NOT NULL,
                author_email VARCHAR(255) NOT NULL,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        print("🗄️ Database 'blog_posts' table initialized or already exists. Ready to ink! 🚀")
    except Exception as e:
        print(f"🚨 Error initializing database table: {e}")
        print("Please ensure your PostgreSQL database is running and accessible with the correct credentials.")
        # In a real application, you might want to log this error and gracefully shut down
    finally:
        if conn:
            conn.close()

# Run database initialization when the application starts
# This will try to connect and create table on app start
with app.app_context():
    init_db()

@app.route('/')
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "InkDrop Backend is humming! 🚀"}), 200

@app.route('/posts', methods=['POST'])
def add_blog_post():
    """Endpoint to add a new blog post."""
    data = request.get_json()
    author_name = data.get('author_name')
    author_email = data.get('author_email')
    title = data.get('title')
    content = data.get('content')

    if not all([author_name, author_email, title, content]):
        return jsonify({"error": "All fields (author_name, author_email, title, content) are required 😟"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO blog_posts (author_name, author_email, title, content) VALUES (%s, %s, %s, %s) RETURNING id, created_at;",
            (author_name, author_email, title, content)
        )
        post_id, created_at = cur.fetchone()
        conn.commit()
        cur.close()
        print(f"Post created: {title} by {author_name}")
        return jsonify({
            "message": "Blog post published successfully! 🎉",
            "id": post_id,
            "author_name": author_name,
            "author_email": author_email,
            "title": title,
            "content": content,
            "created_at": created_at.isoformat() # Convert datetime object to string
        }), 201
    except psycopg2.Error as e:
        print(f"🚨 Database error when adding post: {e}")
        conn.rollback() # Rollback in case of error
        return jsonify({"error": f"Failed to publish blog post due to database error 😔: {str(e)}"}), 500
    except Exception as e:
        print(f"🚨 Unexpected error when adding post: {e}")
        return jsonify({"error": f"An unexpected error occurred 😬: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/posts', methods=['GET'])
def get_blog_posts():
    """Endpoint to retrieve all blog posts."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Order by created_at in descending order for newest first
        cur.execute("SELECT id, author_name, author_email, title, content, created_at FROM blog_posts ORDER BY created_at DESC;")
        posts = cur.fetchall()
        cur.close()
        # Convert list of tuples to list of dictionaries
        posts_list = []
        for post in posts:
            posts_list.append({
                "id": post[0],
                "author_name": post[1],
                "author_email": post[2],
                "title": post[3],
                "content": post[4],
                "created_at": post[5].isoformat() # Convert datetime object to string
            })
        print(f"Fetched {len(posts_list)} blog posts.")
        return jsonify(posts_list), 200
    except psycopg2.Error as e:
        print(f"🚨 Database error when fetching posts: {e}")
        return jsonify({"error": f"Failed to retrieve blog posts from database 😔: {str(e)}"}), 500
    except Exception as e:
        print(f"🚨 Unexpected error when fetching posts: {e}")
        return jsonify({"error": f"An unexpected error occurred 😬: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # When running locally without Docker:
    # Ensure you have a PostgreSQL server running locally
    # and a database named 'inkdrop_db' with user 'inkdrop_user' and password 'inkdrop_password'
    # Or, adjust DB_HOST, DB_NAME, DB_USER, DB_PASSWORD environment variables.
    # Set host='0.0.0.0' to make it accessible from outside the container (useful for Docker)
    app.run(host='0.0.0.0', port=5000, debug=True)