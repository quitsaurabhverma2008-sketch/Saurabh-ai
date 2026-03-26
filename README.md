# Saurabh AI 🚀

An intelligent AI chat application built with FastAPI, HTML/CSS/JS, featuring OTP login, memory system, and multiple AI models.

## Features

- 🤖 AI Chat with multiple models (Groq, Ollama, Pollinations)
- 🔐 OTP Email Login System
- 💾 Full Conversation Memory (v3.0)
- 🌙 Dark/Light Theme
- 📱 Responsive Design
- 🎨 3D Animated Login Page

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Authentication:** JWT + OTP Email
- **AI:** Groq API, Ollama, Pollinations AI

## Local Development

```bash
cd backend
pip install -r requirements.txt
python server.py
```

Visit: http://localhost:8000

## Deployment on PythonAnywhere

### Step 1: Create Account
Go to [pythonanywhere.com](https://www.pythonanywhere.com) and create a free account.

### Step 2: Upload Files
Upload all project files to PythonAnywhere:
- Use Files tab → Upload files
- Or clone from GitHub: `git clone https://github.com/quitsaurabhverma2008-sketch/Saurabh-ai.git`

### Step 3: Create Virtual Environment
Open PythonAnywhere Bash and run:
```bash
mkvirtualenv --python=/usr/bin/python3.11 saurabh-ai
pip install -r requirements.txt
```

### Step 4: Configure Web App
1. Go to Web tab → Add new web app
2. Choose "Manual configuration"
3. Select Python 3.11

### Step 5: Configure Settings
In the Web configuration page:

- **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/saurabh-ai`
- **Working directory:** `/home/YOUR_USERNAME/saurabh-ai`

### Step 6: WSGI Configuration
Edit the WSGI config file and replace with:
```python
import sys
import os

project_home = '/home/YOUR_USERNAME/saurabh-ai'
virtualenv_home = '/home/YOUR_USERNAME/.virtualenvs/saurabh-ai'

sys.path.insert(0, project_home)
os.environ['PYTHONPATH'] = project_home

# Activate virtualenv
os.path.join(virtualenv_home, 'bin', 'activate_this.py')
exec(open(os.path.join(virtualenv_home, 'bin', 'activate_this.py')).read(), dict(__file__=os.path.join(virtualenv_home, 'bin', 'activate_this.py')))

from main import app as application
```

### Step 7: Static Files (Optional)
If needed, configure in Static files section:
- URL: `/static/`
- Path: `/home/YOUR_USERNAME/saurabh-ai/`

### Step 8: Reload
Click "Reload" button on Web tab.

### Step 9: Visit Your Site!
Go to: `https://YOUR_USERNAME.pythonanywhere.com`

## Environment Variables

Set these in your config/api_keys.json:
```json
{
  "groq": ["your-groq-api-keys"],
  "ollama": "http://localhost:11434",
  "pollinations": "your-pollinations-key"
}
```

## Important Notes

1. **API Keys:** Keep your api_keys.json safe and never commit to GitHub
2. **Database:** users.db will be created automatically
3. **Renewal:** Free accounts need renewal every 3 months
4. **Custom Domain:** You can add custom domain in paid plans

## License

MIT

---

Built with ❤️ by Saurabh
