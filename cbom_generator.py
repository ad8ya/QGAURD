from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
from datetime import datetime
import tempfile
import git
import shutil
import subprocess
import os
import json

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
        # Create cbom_components table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cbom_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                component_name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                vulnerability TEXT,
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

# Initialize the database schema at app startup
init_db()

def insert_project(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    upload_date = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO projects (name, upload_date) VALUES (?, ?)",
        (name, upload_date)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id

def insert_cbom_components(project_id, components):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for comp in components:
        cursor.execute(
            "INSERT INTO cbom_components (project_id, component_name, component_type, vulnerability) VALUES (?, ?, ?, ?)",
            (project_id, comp['component_name'], comp['component_type'], comp.get('vulnerability'))
        )
    conn.commit()
    conn.close()

def get_cbom_by_project(project_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT component_name, component_type, vulnerability FROM cbom_components WHERE project_id = ?",
        (project_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"component_name": r[0], "component_type": r[1], "vulnerability": r[2]}
        for r in rows
    ]

def clone_github_repo(github_url):
    temp_dir = tempfile.mkdtemp()
    try:
        git.Repo.clone_from(github_url, temp_dir)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to clone repository: {e}")

def run_codeql_crypto_query(target_dir, codeql_path='codeql'):
    with tempfile.TemporaryDirectory() as db_dir:
        # Create CodeQL database
        create_db_cmd = [
            codeql_path, 'database', 'create', db_dir,
            '--language=python',
            f'--source-root={target_dir}'
        ]
        result = subprocess.run(create_db_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"CodeQL DB creation failed: {result.stderr}")

        # Run CodeQL query (adjust the query path as needed)
        query_path = 'codeql/python-queries:Security/Crypto/UseOfWeakCryptographicAlgorithm.ql'
        output_bqrs = os.path.join(db_dir, 'crypto-results.bqrs')
        analyze_cmd = [
            codeql_path, 'database', 'analyze', db_dir, query_path,
            '--format=bqrs',
            f'--output={output_bqrs}'
        ]
        result = subprocess.run(analyze_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"CodeQL analysis failed: {result.stderr}")

        # Decode BQRS to JSON
        output_json = os.path.join(db_dir, 'crypto-results.json')
        decode_cmd = [
            codeql_path, 'bqrs', 'decode', output_bqrs,
            '--format=json',
            f'--output={output_json}'
        ]
        result = subprocess.run(decode_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"CodeQL BQRS decode failed: {result.stderr}")

        with open(output_json, 'r', encoding='utf-8') as f:
            results = json.load(f)
        return results

@app.route('/api/upload_github', methods=['POST'])
def upload_github():
    data = request.json
    github_url = data.get('github_url')
    if not github_url:
        return jsonify({'error': 'GitHub URL is required'}), 400

    # Simulate project name extraction from URL
    project_name = github_url.rstrip('/').split('/')[-1]
    project_id = insert_project(project_name)
    return jsonify({'project_id': project_id, 'project_name': project_name}), 201

@app.route('/api/analyze_project/<int:project_id>', methods=['POST'])
def analyze_project(project_id):
    data = request.json
    github_url = data.get('github_url')
    if not github_url:
        return jsonify({'error': 'GitHub URL is required'}), 400

    try:
        repo_dir = clone_github_repo(github_url)
        codeql_results = run_codeql_crypto_query(repo_dir)
        # Parse codeql_results and extract relevant CBOM components
        components = []
        # Example parsing (adjust based on actual CodeQL output structure)
        for result in codeql_results.get('runs', []):
            for row in result.get('results', []):
                components.append({
                    "component_name": row.get('name', 'unknown'),
                    "component_type": "crypto",
                    "vulnerability": row.get('message', None)
                })
        insert_cbom_components(project_id, components)
        shutil.rmtree(repo_dir)
        return jsonify({'status': 'Analysis complete', 'components_added': len(components)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cbom/<int:project_id>', methods=['GET'])
def get_cbom(project_id):
    cbom = get_cbom_by_project(project_id)
    return jsonify({'project_id': project_id, 'cbom': cbom})

if __name__ == '__main__':
    app.run(debug=True)