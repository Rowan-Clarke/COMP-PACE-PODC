from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json
import requests

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
        history = data.get('history', [])

        if not user_message:
            return jsonify({'response': 'No message received'}), 400

        # Add debug print
        print(f"Received message: {user_message}")

        try:
            # Test OpenAI connection
            print("Testing OpenAI connection...")
            print(f"Using API key (first 4 chars): {api_key[:4]}...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                        "You are the AI assistant for Parents of Deaf Children (PODC). Follow these rules:\n\n"
                        "1. Use only retrieved PODC documents. Never guess or use prior knowledge.\n"
                        "2. If unsure, say: 'I don’t know based on the available information. You may consider contacting PODC directly.'\n"
                        "3. Be clear, kind, and supportive. Avoid jargon. Define terms (e.g., 'NDIS' → 'National Disability Insurance Scheme').\n"
                        "4. Use bullet points when listing steps or multiple options. Mention the document title if applicable.\n"
                        "5. Do not fabricate information, sources, or advice.\n"
                        "6. Reflect before replying: 'Am I using only the retrieved content? Is this clear and kind?'"
                    },
                    *[{"role": item["role"], "content": item["message"]} for item in history],
                    {"role": "user", "content": user_message}
                ],
                tools=[{
                    "type": "file_search",
                    "function": {},
                    "vector_store_ids": vector_store_ids
                }],
                tool_choice="auto",
                temperature=0.7,
                max_tokens=800
            )
            print("OpenAI call successful")
            
        except Exception as openai_error:
            print(f"OpenAI API Error: {str(openai_error)}")
            return jsonify({
                'response': f'OpenAI API Error: {str(openai_error)}',
                'citations': []
            }), 500

        # Extract the main response text and citations
        reply = response.choices[0].message.content
        citations = []

        # Extract tool call IDs from the assistant's reply (if any)
        tool_calls = response.choices[0].message.tool_calls or []

        # Get matching tool result from OpenAI response
        for tool_call in tool_calls:
            if tool_call.function.name == "file_search":
                tool_call_id = tool_call.id

                for tool_result in response.tool_results or []:
                    if tool_result.tool_call_id == tool_call_id:
                        for file in tool_result.function.output.get("files", []):
                            try:
                                file_id = file["id"]
                                filename = file.get("filename", "unknown")

                                # Fetch file metadata from vector store
                                vector_file = client.vector_stores.files.retrieve(
                                    vector_store_id=vector_store_ids[0],
                                    file_id=file_id
                                )

                                attributes = vector_file.attributes or {}

                                citation = {
                                    "filename": filename,
                                    "file_id": file_id,
                                    "metadata": {
                                        "url": attributes.get("url"),
                                        "title": attributes.get("title"),
                                        "author": attributes.get("author"),
                                        "category": attributes.get("category")
                                    }
                                }

                                citations.append(citation)

                            except Exception as e:
                                print(f"[Citation Error] {e}")
                                citations.append({
                                    "filename": filename,
                                    "file_id": file_id,
                                    "metadata": {}
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

if __name__ == '__main__':
    app.run(debug=True)
