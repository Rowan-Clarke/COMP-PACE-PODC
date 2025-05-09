from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json
import sqlite3
from pathlib import Path

# Load environment variables from .env with debugging
env_path = find_dotenv()
if env_path:
    print(f"Found .env file at: {env_path}")
    load_dotenv(env_path)
else:
    print("No .env file found!")

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5000",
            "https://podc-chatbot-frontend-v2.onrender.com",
            "https://*.onrender.com"
        ],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})


# Set up OpenAI client using the key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No API key found. Please check your .env file")
else:
    print(f"API key loaded")

client = OpenAI(api_key=api_key)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({'response': 'No message received'}), 400

        # Add debug print
        print(f"Received message: {user_message}")

        try:
            # Test OpenAI connection
            print("Testing OpenAI connection...")
            print(f"Using API key (first 4 chars): {api_key[:4]}...")
            
            response = client.responses.create(
                model="gpt-4o-mini",
                instructions="You are a helpful AI assistant for Parents of Deaf Children (PODC). Provide accurate, supportive, and accessible information",
                input=user_message,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": ["vs_681c6bc049b88191897ea7a338837d7c"]
                }],
                include=["file_search_call.results"]
            )
            print("OpenAI call successful")
            
        except Exception as openai_error:
            print(f"OpenAI API Error: {str(openai_error)}")
            return jsonify({
                'response': f'OpenAI API Error: {str(openai_error)}',
                'citations': []
            }), 500

        # Extract the main response text and citations
        reply = ""
        citations = []

        # Process the output items
        for output in response.output:
            if output.type == "message":
                for content in output.content:
                    if content.type == "output_text":
                        reply = content.text
                        # Extract citations from annotations
                        if hasattr(content, 'annotations'):
                            for annotation in content.annotations:
                                if annotation.type == "file_citation":
                                    # Get file info
                                    try:
                                        file_info = client.files.retrieve(annotation.file_id)
                                        print(f"File info for {annotation.filename}:")
                                        print(f"- File ID: {annotation.file_id}")
                                        print(f"- Metadata: {file_info.metadata}")
                                        print(f"- URL: {file_info.metadata.get('url') if hasattr(file_info, 'metadata') else 'No URL'}")
                                        citation = {
                                            'filename': annotation.filename,
                                            'file_id': annotation.file_id,
                                            # Use dictionary-style access for metadata
                                            'metadata': {
                                                'url': file_info.metadata.get('url') if hasattr(file_info, 'metadata') else None,
                                                'category': file_info.metadata.get('category') if hasattr(file_info, 'metadata') else None
                                            }
                                        }
                                        citations.append(citation)
                                    except Exception as e:
                                        print(f"Error retrieving file info: {e}")
                                        # Add citation without metadata if retrieval fails
                                        citations.append({
                                            'filename': annotation.filename,
                                            'file_id': annotation.file_id,
                                            'metadata': {}
                                        })

        return jsonify({
            'response': reply,
            'citations': citations
        })

    except Exception as e:
        print(f"Detailed error: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'response': f'Server error: {str(e)}',
            'citations': []
        }), 500

# Ensure DB exists and create table if needed
DB_FILE = Path("flags.db")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS flagged_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_prompt TEXT,
                flagged_text TEXT
            )
        ''')

# Initialize DB at startup
init_db()

@app.route('/flag', methods=['POST'])
def flag_message():
    try:
        data = request.get_json()
        flagged_text = data.get('flaggedText')
        user_prompt = data.get('userPrompt')
        timestamp = data.get('timestamp')

        print("\n[FLAGGED]")
        print(f"- Time: {timestamp}")
        print(f"- User Prompt: {user_prompt}")
        print(f"- Flagged Response: {flagged_text}")

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('''
                INSERT INTO flagged_responses (timestamp, user_prompt, flagged_text)
                VALUES (?, ?, ?)
            ''', (timestamp, user_prompt, flagged_text))

        return jsonify({"message": "Flag stored in database"}), 200

    except Exception as e:
        print(f"Error storing flag in database: {e}")
        return jsonify({"message": "Failed to store flag"}), 500

@app.route('/flags', methods=['GET'])
def list_flags():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute(
                'SELECT id, timestamp, user_prompt, flagged_text FROM flagged_responses ORDER BY timestamp DESC'
            )
            results = cursor.fetchall()

        flags = [
            {
                "id": row[0],
                "timestamp": row[1],
                "user_prompt": row[2],
                "flagged_text": row[3]
            }
            for row in results
        ]

        return jsonify(flags)

    except Exception as e:
        print(f"Error fetching flags: {e}")
        return jsonify({"message": "Failed to fetch flagged data"}), 500

if __name__ == '__main__':
    app.run(debug=True)
