from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json

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
    r"/chat": {
        "origins": [
            "http://localhost:5000",
            "https://podc-chatbot-frontend-v2.onrender.com",
            "https://*.onrender.com"
        ],
        "methods": ["POST"],
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

if __name__ == '__main__':
    app.run(debug=True)
