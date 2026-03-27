# Saurabh AI

An intelligent AI chat application built with FastAPI, featuring OTP login, memory system, and multiple AI models.

## Features

- AI Chat with multiple models (Groq, Ollama, Pollinations)
- OTP Email Login System
- Full Conversation Memory (v3.0)
- Dark/Light Theme
- Responsive Design
- 3D Animated Login Page

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Authentication:** JWT + OTP Email
- **AI:** Groq API, Ollama, Pollinations AI

## Local Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run server
python server.py
```

Or from root:
```bash
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

## Deployment on PythonAnywhere

### Option 1: Using Consoles (Recommended for Free Tier)

PythonAnywhere free tier doesn't support ASGI apps directly via WSGI. Use Consoles instead:

1. Create account at [pythonanywhere.com](https://www.pythonanywhere.com)

2. Open Bash Console and clone repo:
```bash
git clone https://github.com/quitsaurabhverma2008-sketch/saurabh-ai.git
cd saurabh-ai
```

3. Create virtualenv and install:
```bash
mkvirtualenv --python=/usr/bin/python3.11 saurabh-ai
pip install -r requirements.txt
```

4. Create api_keys.json in config folder

5. Run with uvicorn:
```bash
uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

6. Your app will run but won't be accessible publicly on free tier

### Option 2: Web App (Paid Plans)

For full public deployment, upgrade to PythonAnywhere paid plan:

1. Follow Steps 1-4 from Option 1

2. Go to Web tab → Add new web app

3. Choose "Manual configuration" → Python 3.11

4. Configure WSGI file (see wsgi.py in this repo)

5. Reload web app

### Environment Variables

Create `config/api_keys.json`:
```json
{
  "groq": ["your-groq-api-keys"],
  "ollama": "http://localhost:11434",
  "pollinations": "your-pollinations-key"
}
```

## Alternative: Deploy to Railway/Render

Railway and Render offer free tiers with better ASGI support:

1. Connect your GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`

## Important Notes

1. API Keys: Keep your api_keys.json safe - never commit to GitHub
2. Database: users.db will be created automatically
3. PythonAnywhere: Free accounts need renewal every 3 months

---

Built with by Saurabh
