from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json
import requests

SUPABASE_URL = "https://jqcnepfjbcpgsulzbfna.supabase.co"
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")

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
            "https://*.onrender.com",
            "https://macquarieuniversity.wildapricot.org/", #Change to PODC domain for integration
            "https://*.wildapricot.org"
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
                    "vector_store_ids": ["vs_681eac93bf088191bd4f7de05e04dbbf"]
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
                                    # Get file info from vector store instead of regular files
                                    try:
                                        vector_file = client.vector_stores.files.retrieve(
                                            vector_store_id="vs_681eac93bf088191bd4f7de05e04dbbf",
                                            file_id=annotation.file_id
                                        )
                                        
                                        # Extract URL from attributes if available
                                        url = vector_file.attributes.get('url') if vector_file.attributes else None
                                        
                                        print(f"File info for {annotation.filename}:")
                                        print(f"- File ID: {annotation.file_id}")
                                        print(f"- URL: {url}")
                                        
                                        citation = {
                                            'filename': annotation.filename,
                                            'file_id': annotation.file_id,
                                            'metadata': {
                                                'url': url,
                                                'category': vector_file.attributes.get('category') if vector_file.attributes else None
                                            }
                                        }
                                        citations.append(citation)
                                    except Exception as e:
                                        print(f"Error retrieving file info: {e}")
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

        # POST to Supabase
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "timestamp": timestamp,
            "user_prompt": user_prompt,
            "flagged_text": flagged_text
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/flags",
            headers=headers,
            json=payload
        )

        if response.status_code == 201:
            return jsonify({"message": "Flag stored in Supabase"}), 200
        else:
            print("Supabase error:", response.text)
            return jsonify({"message": "Failed to store flag in Supabase"}), 500

    except Exception as e:
        print(f"Error sending flag: {e}")
        return jsonify({"message": "Internal error storing flag"}), 500

@app.route('/flags', methods=['GET'])
def list_flags():
    try:
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/flags?select=id,timestamp,user_prompt,flagged_text&order=timestamp.desc",
            headers=headers
        )

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            print("Error fetching from Supabase:", response.text)
            return jsonify({"message": "Failed to fetch flags"}), 500

    except Exception as e:
        print(f"Error reading flags from Supabase: {e}")
        return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
