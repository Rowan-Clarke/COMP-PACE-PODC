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

        def generate():
            response = client.responses.create(
                model="gpt-4o-mini",
                instructions="You are a helpful AI assistant for Parents of Deaf Children (PODC). Provide accurate, supportive, and accessible information",
                input=user_message,
                top_p=0.35 # Adjusted to 0.35 for more focused responses
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": ["vs_681a08ffa090819183d5d04745a28952"]
                }],
                include=["file_search_call.results"]  # Include file search results
            )

            # Extract the main response text and citations
            reply = ""
            citations = []

            for chunk in response:
                if chunk.type == "message":
                    for content in chunk.content:
                        if content.type == "output_text":
                            current_response += content.text
                            # Send the chunk immediately
                            yield f"data: {json.dumps({'type': 'text', 'content': content.text})}\n\n"
                            
                        if hasattr(content, 'annotations'):
                            for annotation in content.annotations:
                                if annotation.type == "file_citation":
                                    citations.append({
                                        'filename': annotation.filename,
                                        'file_id': annotation.file_id
                                    })
            
            # Send citations at the end
            if citations:
                yield f"data: {json.dumps({'type': 'citations', 'content': citations})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        print("Error:", e)
        return jsonify({'response': 'Sorry, something went wrong.', 'citations': []}), 500

if __name__ == '__main__':
    app.run(debug=True)
