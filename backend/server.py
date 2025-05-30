from flask import Flask, request, jsonify, Response, stream_with_context, session
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json
import requests
import datetime
import secrets

SUPABASE_URL = "https://jqcnepfjbcpgsulzbfna.supabase.co"
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")
vector_store_ids = ["vs_682b3328e1cc8191ae3c2186a94b18e4"]

# Load environment variables from .env with debugging
env_path = find_dotenv()
if env_path:
    print(f"Found .env file at: {env_path}")
    load_dotenv(env_path)
else:
    print("No .env file found!")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)  # Set session lifetime
app.config['SESSION_PERMANENT'] = True

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
        "allow_headers": ["Content-Type"],
        "supports_credentials": True  # Add this line
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

        # Initialize or get conversation history
        if 'history' not in session:
            session['history'] = []
            print("New conversation started")
        
        history = session.get('history', [])
        print(f"Current history length: {len(history)}")

        # Add user message to history
        history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.datetime.now().isoformat()
        })

        # Build context from history
        context_messages = history[-10:]  # Last 10 messages
        context = ""
        for turn in context_messages:
            prefix = "User:" if turn["role"] == "user" else "Assistant:"
            context += f"{prefix} {turn['content']}\n"

        print(f"Context being sent to API: {context}")
        
        try:
            # Test OpenAI connection
            print("Testing OpenAI connection...")
            print(f"Using API key (first 4 chars): {api_key[:4]}...")
            
            response = client.responses.create(
                model="gpt-4o-mini",
                instructions = (
                    "You are the AI assistant for Parents of Deaf Children (PODC). Follow these rules:\n\n"
                    "1. Use only information retrieved from the PODC Knowledge Base. Do not refer to them as 'uploaded documents'.\n"
                    "2. If unsure, say: 'I don’t know based on the available information. You may consider contacting PODC directly.'\n"
                    "3. Be clear, kind, and supportive. Avoid jargon. Define terms (e.g., 'NDIS' → 'National Disability Insurance Scheme').\n"
                    "4. Use bullet points when listing steps or multiple options. Mention the document title if applicable.\n"
                    "5. Do not fabricate information, sources, or advice.\n"
                    "6. Reflect before replying: 'Am I using only the retrieved content? Is this clear and kind?'\n"
                    "7. Never say 'documents you uploaded' or imply the user provided the information. Instead, say: 'Based on official PODC materials' or 'According to our knowledge base'."
                ),
                # input=user_message.
                input=context,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": vector_store_ids
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
                                            vector_store_id = vector_store_ids[0],  # Use first ID from the list
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
                                                'title': vector_file.attributes.get('title') if vector_file.attributes else None,
                                                'author': vector_file.attributes.get('author') if vector_file.attributes else None,
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

        # After getting the response, update history
        history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Explicitly save history back to session
        session['history'] = history
        session.modified = True  # Mark session as modified
        
        return jsonify({
            'response': reply,
            'citations': citations,
            'history': history
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

@app.route('/feedback', methods=['POST'])
def collect_feedback():
    try:
        data = request.get_json()
        timestamp = data.get('timestamp')
        rating = data.get('rating')
        feedback = data.get('feedback')
        user_prompt = data.get('user_prompt')
        response = data.get('response')

        print("\n[FEEDBACK]")
        print(f"- Rating: {rating}")
        print(f"- Feedback: {feedback}")
        print(f"- User Prompt: {user_prompt}")
        print(f"- Response: {response}")

        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "timestamp": timestamp,
            "rating": rating,
            "feedback": feedback,
            "user_prompt": user_prompt,
            "response": response
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/feedback",
            headers=headers,
            json=payload
        )

        if response.status_code == 201:
            return jsonify({"message": "Feedback stored successfully"}), 200
        else:
            print("Supabase error:", response.text)
            return jsonify({"message": "Failed to store feedback"}), 500

    except Exception as e:
        print(f"Error storing feedback: {e}")
        return jsonify({"message": "Internal error storing feedback"}), 500

@app.route('/end_chat', methods=['POST'])
def end_chat():
    """End the chat session and store the conversation history if needed"""
    try:
        # Get the final conversation history
        final_history = session.get('history', [])
        
        # You could store the conversation history in Supabase here if needed
        if final_history:
            headers = {
                "apikey": SUPABASE_API_KEY,
                "Authorization": f"Bearer {SUPABASE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "conversation_history": final_history,
                "ended_at": datetime.datetime.now().isoformat()
            }
            
            # Store in Supabase (optional)
            requests.post(
                f"{SUPABASE_URL}/rest/v1/conversations",
                headers=headers,
                json=payload
            )
        
        # Clear the session
        session.clear()
        return jsonify({
            "message": "Chat session ended and memory cleared.",
            "status": "success"
        }), 200
        
    except Exception as e:
        print(f"Error ending chat session: {e}")
        return jsonify({
            "message": "Error ending chat session",
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
