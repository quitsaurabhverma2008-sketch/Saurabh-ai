# Saurabh AI 🤖

A powerful personal AI chat application built with FastAPI, featuring **67+ AI models** from GROQ and NVIDIA, memory system, and beautiful UI.

## 🌟 Features

- **67+ AI Models** - GROQ (Llama, Mixtral, Gemma) + NVIDIA (DeepSeek, Phi, Mistral, Llama 4)
- **Smart Model Selection** - Choose from 12 categories (Reasoning, Coding, Vision, Chat, etc.)
- **Full Conversation Memory** - AI remembers your context across chats
- **Password Authentication** - Simple and secure login
- **Dark/Light Theme** - Easy on the eyes
- **Responsive Design** - Works on desktop and mobile
- **Streaming Responses** - Real-time AI replies

## 🚀 Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Authentication:** JWT Tokens
- **AI APIs:** GROQ API, NVIDIA Build API

## 💻 Models Available

| Category | Models | Provider |
|----------|--------|----------|
| Reasoning | DeepSeek R1, Nemotron Super | NVIDIA |
| Coding | DeepSeek V3.2, Qwen3 Coder, Phi-4 | NVIDIA |
| Vision | Llama 4 Scout, InternVL2 | NVIDIA |
| Chat | Llama 4 Maverick, Gemma 3 | NVIDIA |
| General | Sage, Mixtral, LLama 3.3 | GROQ |

**Default Model:** Sage (Llama 3.3 70B) - Fastest GROQ model

## 🖥️ Local Development

```bash
# 1. Clone the repo
git clone https://github.com/quitsaurabhverma2008-sketch/saurabh-ai.git
cd saurabh-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create config file
mkdir config
# Create config/api_keys.json with your API keys

# 4. Run the server
uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

## 🌐 Deployment

### Render (Recommended - Free Tier)

1. Fork this repo to your GitHub
2. Go to [render.com](https://render.com) and sign up
3. Create a new "Web Service"
4. Connect your GitHub repo
5. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `GROQ_API_KEYS` - Your GROQ API keys (comma separated)
   - `NVIDIA_API_KEYS` - Your NVIDIA API keys (comma separated)
7. Deploy!

**Live Demo:** https://saurabh-ai.onrender.com

## 📁 Project Structure

```
saurabh-ai/
├── backend/          # FastAPI server
│   └── server.py     # Main server file
├── auth/             # Authentication handlers
├── config/           # Configuration (API keys)
├── css/              # Stylesheets
├── js/               # JavaScript files
├── static/           # Static assets
├── index.html        # Main frontend
├── main.py           # Entry point
├── requirements.txt  # Python dependencies
├── render.yaml       # Render config
└── README.md
```

## ⚙️ API Keys Setup

Create `config/api_keys.json`:
```json
{
  "groq": ["gsk_xxx1", "gsk_xxx2"],
  "nvidia": ["nvapi-xxx1", "nvapi-xxx2"]
}
```

Or use environment variables:
```bash
export GROQ_API_KEYS="gsk_xxx1,gsk_xxx2"
export NVIDIA_API_KEYS="nvapi-xxx1,nvapi-xxx2"
```

## 🔑 Getting API Keys

**GROQ API Keys:**
1. Visit [console.groq.com](https://console.groq.com/keys)
2. Sign up / Login
3. Create API Key

**NVIDIA API Keys:**
1. Visit [build.nvidia.com](https://build.nvidia.com/settings/api-keys)
2. Sign up / Login (no credit card needed!)
3. Create API Key

## 📝 Login Credentials

- **Email:** uniquegksaurabh@gmail.com
- **Password:** test123

(For demo purposes - change in production!)

## 👨‍💻 Built By

**Saurabh Verma** - Aspiring Developer from India

- GitHub: [@quitsaurabhverma2008-sketch](https://github.com/quitsaurabhverma2008-sketch)
- Email: uniquegksaurabh@gmail.com

---

*Built with ❤️ while learning Python from scratch*
