# PODC AI Chatbot

A responsive chatbot interface for the Parents of Deaf Children (PODC) AI assistant.

## Local Development

### 1. Install dependencies
```sh
pip install -r backend/requirements.txt
```

### 2. Configure API Key
- Create a `.env` file in the root directory
- Add your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxx
```

### 3. Run the Backend Server
```sh
cd backend
python server.py
```

### 4. Open the Frontend
Open `frontend/index.html` in your browser

## Deployment
This project is deployed on Render.com:
- Frontend: Static site hosting
- Backend: Python web service

### Production URLs
- Frontend: https://podc-chatbot-frontend-v1.onrender.com
- Backend: https://podc-chatbot-backend-v1.onrender.com
