from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up OpenAI client using the key from environment
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({'response': 'No message received'}), 400

        response = client.responses.create(
            model="gpt-4o-mini",
            instructions="You are a helpful AI assistant for Parents of Deaf Children (PODC). Provide accurate, supportive, and accessible information",
            input=user_message,
            tools=[{
                "type": "file_search",
                "vector_store_ids": ["vs_68070872a1208191a8d3f5591d19db91"]
            }],
            include=["file_search_call.results"]  # Include file search results
        )

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
                                    citations.append({
                                        'filename': annotation.filename,
                                        'file_id': annotation.file_id
                                    })

        return jsonify({
            'response': reply,
            'citations': citations
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({'response': 'Sorry, something went wrong.', 'citations': []}), 500

if __name__ == '__main__':
    app.run(debug=True)
