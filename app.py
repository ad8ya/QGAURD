from flask import Flask
from flask_cors import CORS
from api import api  # Import the Blueprint from api.py
import sqlite3
import logging

DB_PATH = 'qguard.db'

# Configure logging
logging.basicConfig(
    filename='db_init.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                upload_date TEXT NOT NULL
            )
        ''')
        # Create cbom_components table with PQC fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cbom_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                component_name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                vulnerability TEXT,
                vulnerability_reason TEXT,
                pqc_migration_suggestion TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        print(f"Error initializing database: {e}")

app = Flask(__name__)
CORS(app)

# Configuration settings can be added here
app.config['UPLOAD_FOLDER'] = 'data/uploads'

# Initialize the database schema at app startup
init_db()

# Register the API Blueprint
app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)