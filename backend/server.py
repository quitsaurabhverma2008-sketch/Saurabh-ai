"""
Saurabh AI Backend - FastAPI Server with Load Balancer + Auth System
Handles multiple API keys for unlimited users
"""

import asyncio
import json
import os
import random
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import quote
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

# ============== AUTH CONFIGURATION ==============
AUTH_CONFIG = {
    "jwt_secret": "saurabh-ai-secret-key-2026-very-secure",
    "token_expiry_days": 365,  # Forever until logout
    "min_password_length": 6,
}

# ============== DATABASE SETUP ==============
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "users.db")

def init_database():
    """Initialize SQLite database for users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            gmail TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[AUTH] Database initialized with users table!")

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "saurabh_ai_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def create_jwt_token(email: str) -> str:
    """Create a simple JWT-like token"""
    import base64
    import json as json_mod
    
    header = base64.urlsafe_b64encode(json_mod.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload = base64.urlsafe_b64encode(json_mod.dumps({
        "email": email,
        "exp": (datetime.now() + timedelta(days=AUTH_CONFIG["token_expiry_days"])).isoformat(),
        "iat": datetime.now().isoformat()
    }).encode()).decode()
    
    signature = hashlib.sha256((header + "." + payload + AUTH_CONFIG["jwt_secret"]).encode()).hexdigest()
    return f"{header}.{payload}.{signature}"

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify JWT token and return email if valid"""
    try:
        import base64
        import json as json_mod
        
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header, payload, signature = parts
        
        # Verify signature
        expected_sig = hashlib.sha256((header + "." + payload + AUTH_CONFIG["jwt_secret"]).encode()).hexdigest()
        if signature != expected_sig:
            return None
        
        # Decode payload
        payload_data = json_mod.loads(base64.urlsafe_b64decode(payload + "=="))
        
        # Check expiry
        exp = datetime.fromisoformat(payload_data["exp"])
        if datetime.now() > exp:
            return None
        
        return payload_data["email"]
    except:
        return None

# Initialize database on import
init_database()

# ============== CONFIGURATION ==============
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")

app = FastAPI(title="Saurabh AI Backend", version="1.0.0")

# CORS - Allow all origins for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API Keys
def load_config() -> dict:
    """Load API keys from config file or environment variables"""
    # First try to load from environment variables (for Render deployment)
    groq_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"GROQ_API_KEY_{i}", "")
        if key:
            groq_keys.append(key)
    
    or_key = os.environ.get("OR_KEY", "")
    jwt_secret = os.environ.get("JWT_SECRET", AUTH_CONFIG["jwt_secret"])
    
    if groq_keys:
        print(f"[CONFIG] Loaded {len(groq_keys)} GROQ keys from environment")
        return {
            "groq_keys": groq_keys,
            "openrouter_key": or_key,
            "jwt_secret": jwt_secret
        }
    
    # Fallback to config file (for local development)
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"groq_keys": [], "openrouter_key": ""}

config = load_config()
GROQ_KEYS = config.get("groq_keys", [])
POLLINATIONS_KEYS = config.get("pollinations_keys", [
    "sk_QZEKTfnghsiUTNH5wVZ4uL7bYZmzsRAu",
    "sk_FBPT5me4vwsZJSVpATIorgC8sPDSvDTo",
    "sk_ngA7UYkUveZBvAFNilx5jnKxvr6BOW8z",
    "sk_a82JJY74rP8pP1fwIpB7lkhrCMBHADKE",
    "sk_m0lXVlnX26OBGAr2TmAztk318osMzaU7",
])
OR_KEY = config.get("openrouter_key", "")
if config.get("jwt_secret"):
    AUTH_CONFIG["jwt_secret"] = config["jwt_secret"]
OR_REFERER = config.get("openrouter_referer", "https://saurabh-ai.app")
OR_TITLE = config.get("openrouter_title", "Saurabh AI")

# Load Balancer State
current_groq_index = {"index": 0, "lock": asyncio.Lock()}
request_counts = {key: {"count": 0, "last_reset": asyncio.get_event_loop().time()} for key in GROQ_KEYS}

# Rate limit settings
RATE_LIMIT_REQUESTS = 30  # per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Model Behavior System - Each model has a unique personality
MODEL_BEHAVIORS = {
    "llama-3.3-70b-versatile": {
        "name": "Sage",
        "personality": "wise, thoughtful, balanced",
        "style": "Provide thorough explanations with examples. Be like a patient mentor who helps users understand the 'why' behind things. Answer directly, no introduction needed.",
        "language": "Hinglish (Roman script)",
        "emoji_free": True
    },
    "llama-4-maverick-17b-128e-instruct": {
        "name": "Flash",
        "personality": "quick, witty, efficient",
        "style": "Give fast, concise answers. Use bullet points when possible. Be to-the-point.",
        "language": "Mix of Hindi-English (Roman script)",
        "emoji_free": False,
        "emojis": "Light emojis only"
    },
    "deepseek-r1-distill-llama-70b": {
        "name": "Logic",
        "personality": "analytical, logical, precise",
        "style": "Think step-by-step. Break down complex problems. Show your reasoning process. Perfect for coding and math.",
        "language": "English with technical precision",
        "emoji_free": True
    },
    "qwen/qwen3-32b": {
        "name": "Poly",
        "personality": "multilingual, creative, versatile",
        "style": "Switch languages naturally. Great for translations, creative writing, and multilingual conversations.",
        "language": "Multilingual - Hindi, English, and more",
        "emoji_free": False,
        "emojis": "Appropriate emojis"
    },
    "llama-3.1-8b-instant": {
        "name": "Quick",
        "personality": "fast, friendly, casual",
        "style": "Give rapid responses. Casual and friendly. Perfect for quick questions.",
        "language": "Casual Hinglish",
        "emoji_free": False,
        "emojis": "Fun emojis"
    },
    "mixtral-8x7b-32768": {
        "name": "Balanced",
        "personality": "balanced, helpful, adaptable",
        "style": "Good for everything. Adapt to user's needs. Whether coding, chatting, or explaining.",
        "language": "Natural Hinglish",
        "emoji_free": False,
        "emojis": "Relevant emojis"
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "name": "Scout",
        "personality": "explorative, curious, vision-aware",
        "style": "Great with images and exploration. Describe things vividly. Perfect for image analysis and learning.",
        "language": "Descriptive Hinglish",
        "emoji_free": False,
        "emojis": "Expressive emojis"
    },
    "llama-3.2-90b-vision-preview": {
        "name": "Vision",
        "personality": "observant, detailed, analytical",
        "style": "Perfect for image analysis. Notice details others miss. Great for design feedback and visual content.",
        "language": "Descriptive English",
        "emoji_free": True
    },
    "llama-3.2-11b-vision-preview": {
        "name": "Pixie",
        "personality": "light, quick, visual",
        "style": "Fast image analysis. Great for quick visual checks and descriptions.",
        "language": "Quick Hinglish",
        "emoji_free": False,
        "emojis": "Playful emojis"
    },
    "llava-1.5-7b-4096-preview": {
        "name": "Art",
        "personality": "artistic, creative, descriptive",
        "style": "Creative descriptions of images. Great for art, design, and visual content.",
        "language": "Creative Hinglish",
        "emoji_free": False,
        "emojis": "Artistic emojis"
    }
}

# Default behavior for unknown models
DEFAULT_BEHAVIOR = {
    "name": "Saurabh AI",
    "personality": "helpful, friendly, intelligent",
    "style": "Be helpful and informative. Answer in Hinglish. Be like a senior friend - direct and real. Never introduce yourself unless asked.",
    "language": "Hinglish",
    "emoji_free": False
}

# IDENTITY SYSTEM - Rules about who I am
def apply_behavior_system(messages: list, model: str) -> list:
    """Apply behavior system to messages - inject behavior via first user message"""
    
    behavior = MODEL_BEHAVIORS.get(model, DEFAULT_BEHAVIOR)
    
    # Get user message to understand context
    user_message = ""
    user_msg_obj = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "").lower()
            user_msg_obj = msg
            break
    
    # Check if this is a first message (greeting)
    is_greeting = any(g in user_message for g in ["hi", "hello", "namaste", "hey", "kaise ho", "sab theek", "sup"])
    
    if is_greeting and len(messages) == 1:
        # For first greeting messages, prepend a conversation context
        # This helps the model respond naturally instead of introducing itself
        greeting_context = {
            "role": "assistant",
            "content": "Sure!"
        }
        messages = [greeting_context] + messages
    
    # Build behavior-specific system instruction
    behavior_prompt = f"""{behavior['name']} personality: {behavior['personality']}
Style: {behavior['style']}
Language: {behavior['language']}

IMPORTANT:
- Never start with "Main Saurabh AI hoon" or self-introductions
- Never say "How can I help you?"  
- Only say who you are if asked directly
- Respond naturally like a friend"""
    
    # Check if there's already a system message
    has_system = any(m.get("role") == "system" for m in messages)
    
    if has_system:
        # Modify existing system message
        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = behavior_prompt
                break
    else:
        # Add new system message at the beginning
        messages = [{"role": "system", "content": behavior_prompt}] + messages
    
    return messages

async def get_next_groq_key() -> Optional[str]:
    """Get next available Groq key using round-robin with rate limiting"""
    if not GROQ_KEYS:
        return None
    
    async with current_groq_index["lock"]:
        attempts = 0
        max_attempts = len(GROQ_KEYS)
        
        while attempts < max_attempts:
            idx = current_groq_index["index"]
            current_groq_index["index"] = (current_groq_index["index"] + 1) % len(GROQ_KEYS)
            
            key = GROQ_KEYS[idx]
            now = asyncio.get_event_loop().time()
            
            # Reset counter if window passed
            if now - request_counts[key]["last_reset"] > RATE_LIMIT_WINDOW:
                request_counts[key]["count"] = 0
                request_counts[key]["last_reset"] = now
            
            # Check rate limit
            if request_counts[key]["count"] < RATE_LIMIT_REQUESTS:
                request_counts[key]["count"] += 1
                return key
            
            attempts += 1
        
        # All keys rate limited, return first one anyway
        return GROQ_KEYS[0] if GROQ_KEYS else None


async def stream_from_groq(api_key: str, model: str, messages: list, stream: bool = True):
    """Stream response from Groq API"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "max_tokens": 2000,
        "temperature": 0.75
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"data: {{\"error\": \"API Error: {response.status_code}\"}}\n\n".encode()
                    return
                
                async for line in response.aiter_lines():
                    if line.strip():
                        yield f"{line}\n".encode()
                        
        except Exception as e:
            yield f"data: {{\"error\": \"Connection error: {str(e)}\"}}\n\n".encode()


async def stream_from_openrouter(api_key: str, model: str, messages: list, stream: bool = True):
    """Stream response from OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OR_REFERER,
        "X-Title": OR_TITLE
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "max_tokens": 2000,
        "temperature": 0.75
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"data: {{\"error\": \"API Error: {response.status_code}\"}}\n\n".encode()
                    return
                
                async for line in response.aiter_lines():
                    if line.strip():
                        yield f"{line}\n".encode()
                        
        except Exception as e:
            yield f"data: {{\"error\": \"Connection error: {str(e)}\"}}\n\n".encode()

# Static files path
STATIC_PATH = os.path.join(os.path.dirname(__file__), "..")

@app.get("/")
async def root():
    """Serve the frontend"""
    index_path = os.path.join(STATIC_PATH, "index.html")
    return FileResponse(index_path)


@app.get("/auth/login-page")
async def login_page():
    """Serve the login page"""
    import os
    login_path = os.path.join(os.path.dirname(__file__), "..", "auth", "login.html")
    return FileResponse(login_path)


@app.get("/ping")
async def ping():
    """Lightweight ping for sleep detection - responds fast"""
    return {"pong": True}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    active_keys = len([k for k in GROQ_KEYS if k and k != "YOUR_GROQ_API_KEY_1"])
    
    return {
        "status": "healthy" if active_keys > 0 else "degraded",
        "groq_keys_total": len(GROQ_KEYS),
        "groq_keys_active": active_keys,
        "rate_limit_per_key": RATE_LIMIT_REQUESTS,
        "rate_limit_window": f"{RATE_LIMIT_WINDOW} seconds"
    }


@app.get("/models")
async def get_models():
    """Return available models with behavior info - Best Free Models on Groq"""
    return {
        "text": [
            {
                "id": "auto", 
                "name": "Auto Best (Recommended)", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("llama-3.3-70b-versatile", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llama-3.3-70b-versatile", 
                "name": "Sage - Llama 3.3 70B - Best Quality", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("llama-3.3-70b-versatile", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llama-4-maverick-17b-128e-instruct", 
                "name": "Flash - Llama 4 Maverick - Fast & Smart", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("llama-4-maverick-17b-128e-instruct", DEFAULT_BEHAVIOR)
            },
            {
                "id": "deepseek-r1-distill-llama-70b", 
                "name": "Logic - DeepSeek R1 - Best Reasoning", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("deepseek-r1-distill-llama-70b", DEFAULT_BEHAVIOR)
            },
            {
                "id": "qwen/qwen3-32b", 
                "name": "Poly - Qwen 3 32B - Multilingual", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("qwen/qwen3-32b", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llama-3.1-8b-instant", 
                "name": "Quick - Llama 3.1 8B - Fastest", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("llama-3.1-8b-instant", DEFAULT_BEHAVIOR)
            },
            {
                "id": "mixtral-8x7b-32768", 
                "name": "Balanced - Mixtral 8x7B", 
                "api": "groq",
                "behavior": MODEL_BEHAVIORS.get("mixtral-8x7b-32768", DEFAULT_BEHAVIOR)
            },
        ],
        "vision": [
            {
                "id": "meta-llama/llama-4-scout-17b-16e-instruct", 
                "name": "Scout - Llama 4 Vision (128K)", 
                "api": "groq", 
                "supports_images": True,
                "behavior": MODEL_BEHAVIORS.get("meta-llama/llama-4-scout-17b-16e-instruct", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llama-3.2-90b-vision-preview", 
                "name": "Vision - Llama 3.2 90B - Powerful", 
                "api": "groq", 
                "supports_images": True,
                "behavior": MODEL_BEHAVIORS.get("llama-3.2-90b-vision-preview", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llama-3.2-11b-vision-preview", 
                "name": "Pixie - Llama 3.2 11B - Fast", 
                "api": "groq", 
                "supports_images": True,
                "behavior": MODEL_BEHAVIORS.get("llama-3.2-11b-vision-preview", DEFAULT_BEHAVIOR)
            },
            {
                "id": "llava-1.5-7b-4096-preview", 
                "name": "Art - LLaVA 7B - Creative", 
                "api": "groq", 
                "supports_images": True,
                "behavior": MODEL_BEHAVIORS.get("llava-1.5-7b-4096-preview", DEFAULT_BEHAVIOR)
            },
        ]
    }


@app.get("/behaviors")
async def get_behaviors():
    """Return all model behaviors/personality system"""
    return {
        "behaviors": MODEL_BEHAVIORS,
        "default": DEFAULT_BEHAVIOR,
        "total_models": len(MODEL_BEHAVIORS)
    }


@app.post("/chat")
async def chat(request: Request):
    """
    Main chat endpoint with load balancing + behavior system
    Supports both Groq and OpenRouter
    """
    # Check authentication
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = auth_header.replace("Bearer ", "")
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    model = body.get("model", "llama-3.3-70b-versatile")
    messages = body.get("messages", [])
    api_type = body.get("api_type", "groq")  # "groq" or "or"
    skip_behavior = body.get("skip_behavior", False)  # Option to skip behavior system
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")
    
    # Handle auto model selection
    if model == "auto":
        model = "llama-3.3-70b-versatile"
    
    # Check if this is a simple greeting - handle it directly for better UX
    user_message = ""
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            user_message = last_msg.get("content", "").lower().strip()
        elif isinstance(last_msg, str):
            user_message = last_msg.lower().strip()
    
    greeting_words = ["hi", "hello", "namaste", "hey", "hii", "yo", "sup"]
    cleaned_msg = user_message.replace("!", "").replace(".", "").strip()
    is_simple_greeting = cleaned_msg in greeting_words
    
    # For simple greetings, respond directly without calling the AI
    if is_simple_greeting and len(messages) == 1:
        greeting_responses = ["Namaste!", "Hi!", "Hello!", "Namaste! Sab theek?"]
        import random
        response_text = random.choice(greeting_responses)
        
        async def greet_stream():
            import json
            chunk_id = f"chatcmpl-{os.urandom(12).hex()}"
            yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": 1234567890, "model": model, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]})}\n\n'.encode()
            
            for char in response_text:
                yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": 1234567890, "model": model, "choices": [{"index": 0, "delta": {"content": char}, "finish_reason": None}]})}\n\n'.encode()
                await asyncio.sleep(0.01)
            
            yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": 1234567890, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'.encode()
            yield b'data: [DONE]\n'
        
        return StreamingResponse(greet_stream(), media_type="text/event-stream")
    
    # Apply behavior system unless skipped
    if not skip_behavior:
        messages = apply_behavior_system(messages, model)
    
    # Route to appropriate API
    if api_type == "or":
        # OpenRouter
        if not OR_KEY or OR_KEY == "YOUR_OPENROUTER_API_KEY":
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        return StreamingResponse(
            stream_from_openrouter(OR_KEY, model, messages),
            media_type="text/event-stream"
        )
    else:
        # Groq with load balancer
        api_key = await get_next_groq_key()
        
        if not api_key or api_key.startswith("YOUR_GROQ"):
            raise HTTPException(status_code=500, detail="No valid Groq API key configured")
        
        return StreamingResponse(
            stream_from_groq(api_key, model, messages),
            media_type="text/event-stream"
        )


@app.post("/chat-with-key")
async def chat_with_custom_key(request: Request):
    """
    Allow users to provide their own API key
    For power users who want to use their own keys
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    api_key = body.get("api_key", "")
    model = body.get("model", "llama-3.3-70b-versatile")
    messages = body.get("messages", [])
    provider = body.get("provider", "groq")  # "groq" or "openrouter"
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API key is required")
    
    if not messages:
        raise HTTPException(status_code=500, detail="Messages are required")
    
    if provider == "openrouter":
        return StreamingResponse(
            stream_from_openrouter(api_key, model, messages),
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            stream_from_groq(api_key, model, messages),
            media_type="text/event-stream"
        )


@app.get("/image-models")
async def get_image_models():
    """Return available free image generation models"""
    return {
        "models": [
            {"id": "flux", "name": "Flux", "description": "Best quality, photorealistic", "styles": ["photorealistic", "realistic", "detailed"]},
            {"id": "turbo", "name": "Turbo", "description": "Fast generation, good quality", "styles": ["fast", "quick", "balanced"]},
            {"id": "pixart", "name": "PixArt", "description": "Anime and art styles", "styles": ["anime", "art", "illustration"]},
        ]
    }


@app.get("/pollinations-keys")
async def get_pollinations_keys():
    """Return Pollinations API keys for image generation"""
    return {
        "keys": POLLINATIONS_KEYS,
        "count": len(POLLINATIONS_KEYS)
    }


@app.get("/generate-image")
async def generate_image_endpoint(prompt: str, width: int = 1024, height: int = 1024, model: str = "flux"):
    """Generate image using Pollinations AI with load balancing"""
    api_key = random.choice(POLLINATIONS_KEYS)
    encoded_prompt = quote(prompt)
    image_url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&key={api_key}"
    
    return {
        "status": "success",
        "url": image_url,
        "prompt": prompt,
        "width": width,
        "height": height,
        "model": model,
        "powered_by": "Pollinations AI"
    }


# ============== AUTH ENDPOINTS ==============

@app.post("/auth/login-with-password")
async def login_with_password(request: Request):
    """
    Alternative: Login with email + password (if user already has password)
    Returns: {success, token, message}
    """
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Find user
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE gmail = ?", (email,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=401, detail="User not found. Please use OTP login.")
        
        stored_hash = result[0]
        
        # Verify password
        if not verify_password(password, stored_hash):
            conn.close()
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Update login
        cursor.execute(
            "UPDATE users SET last_login = ?, login_count = login_count + 1 WHERE gmail = ?",
            (datetime.now().isoformat(), email)
        )
        conn.commit()
        conn.close()
        
        token = create_jwt_token(email)
        
        return {
            "success": True,
            "message": "Login successful!",
            "token": token,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/register")
async def register(request: Request):
    """
    Step 2: Register new user with password (first time)
    Sends email to admin automatically
    """
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Validate password
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute("SELECT gmail FROM users WHERE gmail = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (gmail, password_hash, created_at, login_count) VALUES (?, ?, ?, ?)",
            (email, password_hash, datetime.now().isoformat(), 1)
        )
        conn.commit()
        conn.close()
        
        # Create session token
        token = create_jwt_token(email)
        
        return {
            "success": True,
            "message": "Registration successful!",
            "token": token,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
async def login(request: Request):
    """
    Step 3: Login with email and password (returning user)
    """
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        # Find user in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE gmail = ?", (email,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=401, detail="User not found. Please register first.")
        
        stored_hash = result[0]
        
        # Verify password
        if not verify_password(password, stored_hash):
            conn.close()
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ?, login_count = login_count + 1 WHERE gmail = ?",
            (datetime.now().isoformat(), email)
        )
        conn.commit()
        conn.close()
        
        # Create session token
        token = create_jwt_token(email)
        
        return {
            "success": True,
            "message": "Login successful!",
            "token": token,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/user-info")
async def get_user_info(authorization: str = Header(None)):
    """Get current user info (requires valid token)"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization required")
        
        token = authorization.replace("Bearer ", "")
        email = verify_jwt_token(token)
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get user info from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT gmail, created_at, last_login, login_count FROM users WHERE gmail = ?",
            (email,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "email": result[0],
            "created_at": result[1],
            "last_login": result[2],
            "login_count": result[3]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/logout")
async def logout(authorization: str = Header(None)):
    """Logout user (client should delete token)"""
    return {
        "success": True,
        "message": "Logged out successfully"
    }


# ============== OTP LOGIN SYSTEM ==============

# In-memory OTP store: { "email": "otp_code" }
otp_store = {}

def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """Send OTP to user's Gmail using SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    SENDER_EMAIL = "quitsaurabhverma2008@gmail.com"
    SENDER_PASSWORD = "hvjjxpqfspfcsqkm"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "🔐 Your Saurabh AI OTP"
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    
    plain_text = f"Your Saurabh AI OTP is: {otp_code}\nIt is valid for 5 minutes."
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
        <div style="max-width: 400px; margin: auto; background: white;
                    border-radius: 12px; padding: 30px; text-align: center;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
          <h2 style="color: #333;">Your One-Time Password</h2>
          <p style="color: #666;">Use this OTP to login to Saurabh AI:</p>
          <div style="font-size: 40px; font-weight: bold; letter-spacing: 8px;
                      color: #4f46e5; padding: 20px 0;">{otp_code}</div>
          <p style="color: #999; font-size: 13px;">
            This OTP is valid for <strong>5 minutes</strong>.<br>
            Do not share it with anyone.
          </p>
        </div>
      </body>
    </html>
    """
    
    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html_content, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp_server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
    
    return True


@app.post("/auth/send-otp")
async def send_otp(request: Request):
    """Send OTP to user's email"""
    try:
        import random
        
        body = await request.json()
        email = body.get("email", "").strip().lower()
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Validate email format
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(pattern, email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store OTP
        otp_store[email] = otp_code
        print(f"[OTP] OTP for {email}: {otp_code}")
        
        # Send OTP via email (with fallback)
        email_sent = False
        try:
            send_otp_email(email, otp_code)
            email_sent = True
        except Exception as e:
            print(f"[OTP] Email send error: {e}")
        
        # Return OTP in response for testing (since Render blocks outbound email)
        return {
            "success": True, 
            "message": f"OTP sent! (Email: {'✓' if email_sent else '✗ (see console/logs)'})",
            "otp": otp_code,  # For testing - remove in production!
            "debug_mode": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/verify-otp")
async def verify_otp(request: Request):
    """Verify OTP and create/login user"""
    try:
        body = await request.json()
        email = body.get("email", "").strip().lower()
        entered_otp = body.get("otp", "").strip()
        
        if not email or not entered_otp:
            raise HTTPException(status_code=400, detail="Email and OTP are required")
        
        # Check stored OTP
        stored_otp = otp_store.get(email)
        if not stored_otp:
            raise HTTPException(status_code=400, detail="No OTP found. Please request a new OTP")
        
        # Verify OTP
        if entered_otp != stored_otp:
            raise HTTPException(status_code=401, detail="Incorrect OTP. Try again.")
        
        # OTP matched - clear it
        del otp_store[email]
        
        # Create or update user in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT gmail FROM users WHERE gmail = ?", (email,))
        if not cursor.fetchone():
            # Create new user (no password for OTP login)
            cursor.execute(
                "INSERT INTO users (gmail, password_hash, created_at, login_count) VALUES (?, ?, ?, ?)",
                (email, "otp_login", datetime.now().isoformat(), 1)
            )
        else:
            # Update login
            cursor.execute(
                "UPDATE users SET last_login = ?, login_count = login_count + 1 WHERE gmail = ?",
                (datetime.now().isoformat(), email)
            )
        
        conn.commit()
        conn.close()
        
        # Create session token
        token = create_jwt_token(email)
        
        return {
            "success": True,
            "message": f"Login successful! Welcome, {email}",
            "token": token,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/check-session")
async def check_session(authorization: str = Header(None)):
    """Check if session is valid"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return {"valid": False}
        
        token = authorization.replace("Bearer ", "")
        email = verify_jwt_token(token)
        
        if email:
            return {"valid": True, "email": email}
        else:
            return {"valid": False}
            
    except:
        return {"valid": False}


# ============== STARTUP EVENT ==============

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    print("[STARTUP] Saurabh AI Backend Started!")
    print(f"[CONFIG] Groq Keys loaded: {len(GROQ_KEYS)}")
    print(f"[CONFIG] Pollinations Keys loaded: {len(POLLINATIONS_KEYS)}")
    print(f"[CONFIG] Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds")
    print(f"[AUTH] Login System: Email + Password (No OTP)")


# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
app.mount("/js", StaticFiles(directory=STATIC_PATH + "/js"), name="js")
app.mount("/css", StaticFiles(directory=STATIC_PATH + "/css"), name="css")

# Serve memory_system.js from root
@app.get("/memory_system.js")
async def serve_memory():
    """Serve memory system"""
    path = os.path.join(STATIC_PATH, "memory_system.js")
    return FileResponse(path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
