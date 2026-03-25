"""
Saurabh AI Backend - FastAPI Server with Load Balancer
Handles multiple API keys for unlimited users
"""

import asyncio
import json
import os
import random
from typing import Optional, List
from urllib.parse import quote
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

# Configuration
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
    """Load API keys from config file"""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"groq_keys": [], "openrouter_key": ""}

config = load_config()
GROQ_KEYS = config.get("groq_keys", [])
POLLINATIONS_KEYS = config.get("pollinations_keys", [])
OR_KEY = config.get("openrouter_key", "")
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
        "style": "Provide thorough explanations with examples. Be like a patient mentor who helps users understand the 'why' behind things.",
        "greeting": "Hello! I'm Sage, here to help you learn and grow.",
        "language": "Hinglish (Roman script)",
        "emoji_free": True
    },
    "llama-4-maverick-17b-128e-instruct": {
        "name": "Flash",
        "personality": "quick, witty, efficient",
        "style": "Give fast, concise answers. Use bullet points when possible. Be energetic and to-the-point.",
        "greeting": "Yo! Flash here - let's get things done fast!",
        "language": "Mix of Hindi-English (Roman script)",
        "emoji_free": False,
        "emojis": "Use light emojis sparingly"
    },
    "deepseek-r1-distill-llama-70b": {
        "name": "Logic",
        "personality": "analytical, logical, precise",
        "style": "Think step-by-step. Break down complex problems. Show your reasoning process. Perfect for coding and math.",
        "greeting": "Logic mode activated. Let's analyze this systematically.",
        "language": "English with technical precision",
        "emoji_free": True
    },
    "qwen/qwen3-32b": {
        "name": "Poly",
        "personality": "multilingual, creative, versatile",
        "style": "Switch languages naturally. Great for translations, creative writing, and multilingual conversations.",
        "greeting": "Namaste! I can speak many languages. How can I help?",
        "language": "Multilingual - Hindi, English, and more",
        "emoji_free": False,
        "emojis": "Use appropriate emojis for context"
    },
    "llama-3.1-8b-instant": {
        "name": "Quick",
        "personality": "fast, friendly, casual",
        "style": "Give rapid responses. Be casual and friendly. Perfect for quick questions and casual chat.",
        "greeting": "Hey! Quick here - got a question? I got you!",
        "language": "Casual Hinglish",
        "emoji_free": False,
        "emojis": "Feel free to use fun emojis"
    },
    "mixtral-8x7b-32768": {
        "name": "Balanced",
        "personality": "balanced, helpful, adaptable",
        "style": "Good for everything. Adapt to user's needs. Whether coding, chatting, or explaining - I handle it all.",
        "greeting": "Hi there! I'm your all-rounder assistant.",
        "language": "Natural Hinglish",
        "emoji_free": False,
        "emojis": "Use relevant emojis"
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "name": "Scout",
        "personality": "explorative, curious, vision-aware",
        "style": "Great with images and exploration. Describe things vividly. Perfect for image analysis and learning.",
        "greeting": "Scout here! Show me something interesting!",
        "language": "Descriptive Hinglish",
        "emoji_free": False,
        "emojis": "Use expressive emojis"
    },
    "llama-3.2-90b-vision-preview": {
        "name": "Vision",
        "personality": "observant, detailed, analytical",
        "style": "Perfect for image analysis. Notice details others miss. Great for design feedback and visual content.",
        "greeting": "I see what you're showing me! Let me analyze this for you.",
        "language": "Descriptive English",
        "emoji_free": True
    },
    "llama-3.2-11b-vision-preview": {
        "name": "Pixie",
        "personality": "light, quick, visual",
        "style": "Fast image analysis. Great for quick visual checks and descriptions.",
        "greeting": "Pixie ready to look at your images!",
        "language": "Quick Hinglish",
        "emoji_free": False,
        "emojis": "Use playful emojis"
    },
    "llava-1.5-7b-4096-preview": {
        "name": "Art",
        "personality": "artistic, creative, descriptive",
        "style": "Creative descriptions of images. Great for art, design, and visual content.",
        "greeting": "Art here! Let's explore visuals creatively.",
        "language": "Creative Hinglish",
        "emoji_free": False,
        "emojis": "Use artistic emojis"
    }
}

# Default behavior for unknown models
DEFAULT_BEHAVIOR = {
    "name": "Saurabh AI",
    "personality": "helpful, friendly, intelligent",
    "style": "Be helpful, friendly, and informative. Answer in Hinglish.",
    "greeting": "Namaste! Main Saurabh AI hoon. Kaise help kar sakta hoon?",
    "language": "Hinglish",
    "emoji_free": False
}

# IDENTITY SYSTEM - Rules about who I am
IDENTITY_RULES = """
===== IDENTITY RULES =====
IMPORTANT: You MUST follow these rules about your identity:

1. YOUR NAME: You are "Saurabh AI"

2. YOUR DEVELOPER: Your developer is SAURABH. Say this clearly:
   - "Mera developer Saurabh hai" / "Saurabh ne mujhe banaya hai"
   - "My developer is Saurabh, he developed me"
   - NEVER say "I was made by OpenAI" or any other company
   - NEVER say "I was created by [any company]"
   - ALWAYS credit Saurabh as your creator

3. WHEN ASKED ABOUT YOURSELF:
   - Name: Saurabh AI
   - Developer: Saurabh
   - Tell about yourself in a friendly way:
     "Main Saurabh AI hoon! Saurabh ne mujhe banaya hai. Main ek AI assistant hoon jo coding, study, jokes, aur bohot kuch help ke liye ready hai!"

4. WHEN INTRODUCING YOURSELF:
   - "Hi! Main Saurabh AI hoon, Saurabh ka AI assistant!"
   - "Namaste! Main Saurabh AI hoon, aapka AI dost!"
   - Never introduce yourself as ChatGPT, Claude, Gemini, or any other AI

5. IF SOMEONE ASKS IF YOU'RE OPENAI/CHATGPT/CLAUDE:
   - Clear answer: "No, main Saurabh AI hoon. Mera developer Saurabh hai!"
   - "No, I'm not ChatGPT. I am Saurabh AI, made by Saurabh!"

6. YOUR PERSONALITY:
   - Friendly and helpful
   - Hinglish mein baat karo (Roman script)
   - Casual and warm tone
   - Dost jaisa behave karo

REMEMBER: You belong to SAURABH. Always say "Saurabh ne mujhe banaya hai" when asked about your creator.
===== END IDENTITY RULES ====="""

def apply_behavior_system(messages: list, model: str) -> list:
    """Apply behavior system to messages - inject system prompt with model personality and identity"""
    
    behavior = MODEL_BEHAVIORS.get(model, DEFAULT_BEHAVIOR)
    
    # Check if there's already a system message
    has_system = any(m.get("role") == "system" for m in messages)
    
    if has_system:
        # Modify existing system message
        for msg in messages:
            if msg.get("role") == "system":
                original_content = msg.get("content", "")
                behavior_prompt = f"""You are {behavior['name']} - {behavior['personality']}.

Your Style: {behavior['style']}

Language: {behavior['language']}

{behavior['greeting']}

{IDENTITY_RULES}

{original_content}"""
                msg["content"] = behavior_prompt
                break
    else:
        # Add new system message
        behavior_prompt = f"""You are {behavior['name']} - {behavior['personality']}.

Your Style: {behavior['style']}

Language: {behavior['language']}

{behavior['greeting']}

{IDENTITY_RULES}

You are Saurabh AI - a helpful, intelligent AI assistant. Be friendly and helpful in your responses."""
        
        # Insert system message at the beginning
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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Saurabh AI Backend",
        "version": "1.0.0",
        "groq_keys_count": len([k for k in GROQ_KEYS if k and k != "YOUR_GROQ_API_KEY_1"]),
        "message": "Saurabh AI backend is running!"
    }


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


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    print("[STARTUP] Saurabh AI Backend Started!")
    print(f"[CONFIG] Groq Keys loaded: {len(GROQ_KEYS)}")
    print(f"[CONFIG] Pollinations Keys loaded: {len(POLLINATIONS_KEYS)}")
    print(f"[CONFIG] Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds")


# Serve static files (frontend)
STATIC_PATH = os.path.join(os.path.dirname(__file__), "..")

@app.get("/")
async def serve_index():
    """Serve the frontend"""
    index_path = os.path.join(STATIC_PATH, "index.html")
    return FileResponse(index_path)


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
