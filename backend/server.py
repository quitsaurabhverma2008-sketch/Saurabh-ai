"""
Saurabh AI Backend - FastAPI Server with Load Balancer + NVIDIA Integration
Handles GROQ + NVIDIA APIs with 20 total keys + Smart AI Model Selection
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
    "token_expiry_days": 365,
    "min_password_length": 6,
}

# ============== DATABASE SETUP ==============
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "users.db")

def init_database():
    """Initialize SQLite database for users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    print("[AUTH] Database initialized!")

def hash_password(password: str) -> str:
    salt = "saurabh_ai_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def create_jwt_token(email: str) -> str:
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
    try:
        import base64
        import json as json_mod
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        expected_sig = hashlib.sha256((header + "." + payload + AUTH_CONFIG["jwt_secret"]).encode()).hexdigest()
        if signature != expected_sig:
            return None
        payload_data = json_mod.loads(base64.urlsafe_b64decode(payload + "=="))
        exp = datetime.fromisoformat(payload_data["exp"])
        if datetime.now() > exp:
            return None
        return payload_data["email"]
    except:
        return None

init_database()

# ============== CONFIGURATION ==============
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")

app = FastAPI(title="Saurabh AI Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config() -> dict:
    groq_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"GROQ_API_KEY_{i}", "")
        if key:
            groq_keys.append(key)
    
    nvidia_keys = []
    for i in range(1, 11):
        key = os.environ.get(f"NVIDIA_API_KEY_{i}", "")
        if key:
            nvidia_keys.append(key)
    
    if groq_keys or nvidia_keys:
        return {
            "groq_keys": groq_keys,
            "nvidia_keys": nvidia_keys,
        }
    
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"groq_keys": [], "nvidia_keys": []}

config = load_config()
GROQ_KEYS = config.get("groq_keys", [])
NVIDIA_KEYS = config.get("nvidia_keys", [])

# Load Balancer State
current_groq_index = {"index": 0, "lock": asyncio.Lock()}
current_nvidia_index = {"index": 0, "lock": asyncio.Lock()}

# Rate limit settings
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60

# ============== NVIDIA MODEL DATA ==============
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# All 92 NVIDIA Models with Categories and Rankings
NVIDIA_MODELS = {
    # REASONING MODELS
    "deepseek-ai/deepseek-v3.2": {
        "name": "DeepSeek V3.2",
        "category": "reasoning",
        "rank": 1,
        "runs": "16.73M",
        "description": "685B reasoning LLM with sparse attention",
        "context": "128K"
    },
    "moonshotai/kimi-k2-instruct": {
        "name": "Kimi K2",
        "category": "reasoning",
        "rank": 2,
        "runs": "21.48M",
        "description": "Mixture-of-experts with strong reasoning",
        "context": "128K"
    },
    "deepseek-ai/deepseek-v3.1": {
        "name": "DeepSeek V3.1",
        "category": "reasoning",
        "rank": 3,
        "runs": "12.72M",
        "description": "Fast reasoning, 128K context",
        "context": "128K"
    },
    "moonshotai/kimi-k2-instruct-0905": {
        "name": "Kimi K2 Long",
        "category": "long_context",
        "rank": 1,
        "runs": "12.96M",
        "description": "Longer context window, enhanced reasoning",
        "context": "256K"
    },
    "qwen/qwq-32b": {
        "name": "QwQ-32B",
        "category": "reasoning",
        "rank": 4,
        "runs": "3.7M",
        "description": "Reasoning model for hard problems",
        "context": "32K"
    },
    "deepseek-ai/deepseek-r1": {
        "name": "DeepSeek R1",
        "category": "reasoning",
        "rank": 5,
        "runs": "High",
        "description": "State-of-art reasoning model",
        "context": "64K"
    },
    "marin/marin-8b-instruct": {
        "name": "Marin 8B",
        "category": "reasoning",
        "rank": 6,
        "runs": "472K",
        "description": "Reasoning, math, and science",
        "context": "8K"
    },
    
    # CODING MODELS (Verified working)
    "mistralai/devstral-2-123b-instruct-2512": {
        "name": "Devstral 123B",
        "category": "coding",
        "rank": 1,
        "runs": "5.86M",
        "description": "SoTA open code model, 256K context",
        "context": "256K"
    },
    "qwen/qwen3-coder-480b-a35b-instruct": {
        "name": "Qwen3 Coder 480B",
        "category": "coding",
        "rank": 2,
        "runs": "3.76M",
        "description": "Agentic coding, 256K context",
        "context": "256K"
    },
    "qwen/qwen2.5-coder-7b-instruct": {
        "name": "Qwen2.5 Coder 7B",
        "category": "coding",
        "rank": 3,
        "runs": "580K",
        "description": "Mid-size code model",
        "context": "32K"
    },
    "mistralai/mamba-codestral-7b-v0.1": {
        "name": "Codestral 7B",
        "category": "coding",
        "rank": 4,
        "runs": "571K",
        "description": "Code completion model",
        "context": "32K"
    },
    
    # TOOL CALLING / AGENTIC
    # DeepSeek V3.1-T removed - returns 404
    "mistralai/mistral-nemotron": {
        "name": "Mistral Nemotron",
        "category": "tool_calling",
        "rank": 2,
        "runs": "891K",
        "description": "Agentic workflows, function calling",
        "context": "128K"
    },
    "stepfun-ai/step-3.5-flash": {
        "name": "Step 3.5 Flash",
        "category": "agentic",
        "rank": 1,
        "runs": "9.48M",
        "description": "200B reasoning engine, agentic AI",
        "context": "128K"
    },
    "bytedance/seed-oss-36b-instruct": {
        "name": "Seed-OSS 36B",
        "category": "agentic",
        "rank": 2,
        "runs": "3.68M",
        "description": "Long-context, reasoning, agentic",
        "context": "128K"
    },
    "moonshotai/kimi-k2-thinking": {
        "name": "Kimi K2 Thinking",
        "category": "agentic",
        "rank": 3,
        "runs": "3.57M",
        "description": "Native INT4, enhanced tool use",
        "context": "256K"
    },
    
    # VISION MODELS
    "google/gemma-3-27b-it": {
        "name": "Gemma 3 27B",
        "category": "vision",
        "rank": 1,
        "runs": "6.37M",
        "description": "Google's best open multimodal model",
        "context": "8K"
    },
    "meta/llama-4-scout-17b-16e-instruct": {
        "name": "Llama 4 Scout",
        "category": "vision",
        "rank": 2,
        "runs": "24K",
        "description": "10M context, multimodal",
        "context": "10M"
    },
    "meta/llama-4-maverick-17b-128e-instruct": {
        "name": "Llama 4 Maverick",
        "category": "vision",
        "rank": 3,
        "runs": "6.19M",
        "description": "General purpose multimodal",
        "context": "128K"
    },
    "nvidia/cosmos-nemotron-34b": {
        "name": "Cosmos Nemotron",
        "category": "vision",
        "rank": 4,
        "runs": "14",
        "description": "Text/img/video understanding",
        "context": "8K"
    },
    "microsoft/phi-3.5-vision-instruct": {
        "name": "Phi-3.5 Vision",
        "category": "vision",
        "rank": 5,
        "runs": "614K",
        "description": "Multimodal reasoning from images",
        "context": "4K"
    },
    "google/google-paligemma": {
        "name": "PaliGemma",
        "category": "vision",
        "rank": 6,
        "runs": "243K",
        "description": "Vision language model",
        "context": "2K"
    },
    "google/gemma-2-27b-it": {
        "name": "Gemma 2 27B",
        "category": "vision",
        "rank": 7,
        "runs": "877K",
        "description": "Text, code, vision",
        "context": "8K"
    },
    "nvidia/internvl2-14b": {
        "name": "InternVL2 14B",
        "category": "vision",
        "rank": 8,
        "runs": "High",
        "description": "Strong vision-language",
        "context": "8K"
    },
    
    # CHAT / GENERAL MODELS
    "mistralai/mistral-large-3-675b-instruct-2512": {
        "name": "Mistral Large 3",
        "category": "chat",
        "rank": 1,
        "runs": "7.42M",
        "description": "State-of-art general purpose MoE VLM",
        "context": "128K"
    },
    "mistralai/mistral-small-3.1-24b-instruct-2503": {
        "name": "Mistral Small 3.1",
        "category": "chat",
        "rank": 2,
        "runs": "2.35M",
        "description": "Efficient, multilingual, fast",
        "context": "32K"
    },
    "mistralai/mistral-medium-3-instruct": {
        "name": "Mistral Medium 3",
        "category": "chat",
        "rank": 3,
        "runs": "4.75M",
        "description": "Enterprise multimodal",
        "context": "128K"
    },
    "microsoft/phi-3.5-mini-instruct": {
        "name": "Phi-3.5 Mini",
        "category": "chat",
        "rank": 4,
        "runs": "7.88M",
        "description": "Multilingual, fast",
        "context": "128K"
    },
    "mistralai/mistral-7b-instruct-v0.2": {
        "name": "Mistral 7B",
        "category": "chat",
        "rank": 5,
        "runs": "538K",
        "description": "Instruction following, creative text",
        "context": "8K"
    },
    "google/gemma-7b": {
        "name": "Gemma 7B",
        "category": "chat",
        "rank": 6,
        "runs": "656K",
        "description": "Text understanding, code generation",
        "context": "8K"
    },
    "mediatek/breeze-7b-instruct": {
        "name": "Breeze 7B",
        "category": "chat",
        "rank": 7,
        "runs": "443K",
        "description": "Traditional Chinese focus",
        "context": "8K"
    },
    "rakuten/rakutenai-7b-chat": {
        "name": "RakutenAI 7B",
        "category": "chat",
        "rank": 8,
        "runs": "442K",
        "description": "Reasoning, text generation",
        "context": "8K"
    },
    "qwen/qwen2-7b-instruct": {
        "name": "Qwen2 7B",
        "category": "chat",
        "rank": 9,
        "runs": "630K",
        "description": "Chinese/English, coding, math",
        "context": "8K"
    },
    "ai21labs/jamba-1.5-mini-instruct": {
        "name": "Jamba 1.5 Mini",
        "category": "chat",
        "rank": 10,
        "runs": "489K",
        "description": "MoE based LLM",
        "context": "8K"
    },
    
    # MULTILINGUAL MODELS
    "thudm/chatglm3-6b": {
        "name": "ChatGLM3 6B",
        "category": "multilingual",
        "rank": 1,
        "runs": "454K",
        "description": "Chinese/English, translation",
        "context": "8K"
    },
    "baichuan-inc/baichuan2-13b-chat": {
        "name": "Baichuan 2 13B",
        "category": "multilingual",
        "rank": 2,
        "runs": "453K",
        "description": "Chinese/English chat, coding, math",
        "context": "4K"
    },
    
    # EMBEDDINGS MODELS
    "nvidia/nv-embed-v1": {
        "name": "NV-Embed v1",
        "category": "embeddings",
        "rank": 1,
        "runs": "3.11M",
        "description": "High-quality text embeddings",
        "context": "N/A"
    },
    "nvidia/nv-embedcode-7b-v1": {
        "name": "NV-EmbedCode 7B",
        "category": "embeddings",
        "rank": 2,
        "runs": "231K",
        "description": "Code retrieval embeddings",
        "context": "N/A"
    },
    
    # SAFETY MODELS
    "meta/llama-guard-4-12b": {
        "name": "Llama Guard 4",
        "category": "safety",
        "rank": 1,
        "runs": "431K",
        "description": "Safety classification",
        "context": "8K"
    },
    "ibm/granite-guardian-3.0-8b": {
        "name": "Granite Guardian 3.0",
        "category": "safety",
        "rank": 2,
        "runs": "418K",
        "description": "Jailbreak, bias, violence detection",
        "context": "8K"
    },
    "nvidia/nemotron-content-safety-reasoning-4b": {
        "name": "Nemotron Safety 4B",
        "category": "safety",
        "rank": 3,
        "runs": "517K",
        "description": "Context-aware safety reasoning",
        "context": "4K"
    },
    
    # TRANSLATION MODELS
    "nvidia/riva-translate-4b-instruct-v1_1": {
        "name": "Riva Translate 4B",
        "category": "translation",
        "rank": 1,
        "runs": "492K",
        "description": "12 languages translation",
        "context": "4K"
    },
    
    # TTS MODELS
    "nvidia/magpie-tts-flow": {
        "name": "Magpie TTS Flow",
        "category": "tts",
        "rank": 1,
        "runs": "885",
        "description": "Expressive text-to-speech",
        "context": "N/A"
    },
    "nvidia/magpie-tts-zeroshot": {
        "name": "Magpie TTS Zeroshot",
        "category": "tts",
        "rank": 2,
        "runs": "1.5K",
        "description": "Zero-shot voice cloning TTS",
        "context": "N/A"
    },
    
    # OTHER SPECIALIZED MODELS
    "nvidia/nv-dinov2": {
        "name": "NV-DINOv2",
        "category": "vision",
        "rank": 9,
        "runs": "1.24M",
        "description": "Visual foundation model embeddings",
        "context": "N/A"
    },
    "nvidia/llama-3.1-nemotron-ultra-253b-v1": {
        "name": "Nemotron Ultra",
        "category": "reasoning",
        "rank": 7,
        "runs": "High",
        "description": "NVIDIA's best general model",
        "context": "128K"
    },
    "nvidia/llama-3.3-nemotron-super-49b-v1": {
        "name": "Nemotron Super",
        "category": "reasoning",
        "rank": 8,
        "runs": "High",
        "description": "Strong math performance",
        "context": "64K"
    },
    "openai/gpt-oss-120b": {
        "name": "GPT-OSS 120B",
        "category": "reasoning",
        "rank": 9,
        "runs": "High",
        "description": "Largest open-weight model",
        "context": "32K"
    },
    "google/gemma-3n-e2b-it": {
        "name": "Gemma 3N E2B",
        "category": "chat",
        "rank": 11,
        "runs": "614K",
        "description": "Edge computing AI, text/audio/image",
        "context": "8K"
    },
    "google/gemma-3n-e4b-it": {
        "name": "Gemma 3N E4B",
        "category": "chat",
        "rank": 12,
        "runs": "716K",
        "description": "Edge computing AI",
        "context": "8K"
    },
    "mistralai/magistral-small-2506": {
        "name": "Magistral Small",
        "category": "coding",
        "rank": 9,
        "runs": "3.6M",
        "description": "High performance reasoning",
        "context": "32K"
    },
    "nvidia/nemotron-4-mini-hindi-4b-instruct": {
        "name": "Nemotron Hindi 4B",
        "category": "multilingual",
        "rank": 3,
        "runs": "543K",
        "description": "Hindi-English bilingual",
        "context": "4K"
    },
    "nvidia/nemotron-mini-4b-instruct": {
        "name": "Nemotron Mini 4B",
        "category": "chat",
        "rank": 13,
        "runs": "494K",
        "description": "On-device inference, RAG",
        "context": "4K"
    },
    "microsoft/phi-3-medium-128k-instruct": {
        "name": "Phi-3 Medium 128K",
        "category": "long_context",
        "rank": 2,
        "runs": "467K",
        "description": "Lightweight, high-quality reasoning",
        "context": "128K"
    },
    "microsoft/phi-3-small-128k-instruct": {
        "name": "Phi-3 Small 128K",
        "category": "long_context",
        "rank": 3,
        "runs": "489K",
        "description": "Long context, reasoning",
        "context": "128K"
    },
    "microsoft/phi-4-mini-flash-reasoning": {
        "name": "Phi-4 Flash Reasoning",
        "category": "reasoning",
        "rank": 10,
        "runs": "451K",
        "description": "Edge reasoning model",
        "context": "4K"
    },
    "microsoft/phi-4-multimodal-instruct": {
        "name": "Phi-4 Multimodal",
        "category": "vision",
        "rank": 10,
        "runs": "454K",
        "description": "Image and audio understanding",
        "context": "16K"
    },
    "upstage/solar-10.7b-instruct": {
        "name": "Solar 10.7B",
        "category": "reasoning",
        "rank": 11,
        "runs": "459K",
        "description": "Instruction-following, reasoning, math",
        "context": "4K"
    },
    "speakleash/bielik-11b-v2.6-instruct": {
        "name": "Bielik 11B",
        "category": "chat",
        "rank": 14,
        "runs": "450K",
        "description": "Polish language processing",
        "context": "8K"
    },
    "aisingapore/sea-lion-7b-instruct": {
        "name": "Sea Lion 7B",
        "category": "chat",
        "rank": 15,
        "runs": "Low",
        "description": "Southeast Asian languages",
        "context": "8K"
    },
}

# GROQ Model Behaviors
GROQ_MODEL_BEHAVIORS = {
    "llama-3.3-70b-versatile": {
        "name": "Sage",
        "category": "chat",
        "rank": 1,
        "description": "Best quality, balanced",
        "emoji_free": True
    },
    "qwen/qwen3-32b": {
        "name": "Poly",
        "category": "multilingual",
        "rank": 1,
        "description": "Multilingual, creative",
        "emoji_free": False
    },
    "llama-3.1-8b-instant": {
        "name": "Quick",
        "category": "chat",
        "rank": 2,
        "description": "Fastest responses",
        "emoji_free": False
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "name": "Scout",
        "category": "vision",
        "rank": 1,
        "description": "128K context, vision",
        "emoji_free": False
    },
    "moonshotai/kimi-k2-instruct": {
        "name": "Kimi K2",
        "category": "reasoning",
        "rank": 1,
        "description": "MoE, 128K, all-rounder",
        "emoji_free": False
    },
    "moonshotai/kimi-k2-instruct-0905": {
        "name": "Kimi K2 Long",
        "category": "long_context",
        "rank": 1,
        "description": "256K context",
        "emoji_free": False
    },
    "openai/gpt-oss-120b": {
        "name": "GPT-OSS",
        "category": "reasoning",
        "rank": 2,
        "description": "Large open-weight model",
        "emoji_free": True
    },
    "groq/compound": {
        "name": "Compound",
        "category": "chat",
        "rank": 3,
        "description": "Groq's compound model",
        "emoji_free": False
    },
}

# ============== CATEGORY SYSTEM ==============
CATEGORIES = {
    "reasoning": {"name": "Reasoning", "icon": "🧠", "description": "Math, logic, problem-solving"},
    "coding": {"name": "Coding", "icon": "💻", "description": "Code, scripts, debugging"},
    "vision": {"name": "Vision", "icon": "👁️", "description": "Image analysis, multimodal"},
    "chat": {"name": "Chat", "icon": "💬", "description": "General conversation"},
    "tool_calling": {"name": "Tool Calling", "icon": "🔧", "description": "Function calling, agents"},
    "agentic": {"name": "Agentic", "icon": "🤖", "description": "Autonomous agents"},
    "long_context": {"name": "Long Context", "icon": "📚", "description": "Large documents"},
    "multilingual": {"name": "Multilingual", "icon": "🌍", "description": "Translations"},
    "safety": {"name": "Safety", "icon": "🛡️", "description": "Content moderation"},
    "embeddings": {"name": "Embeddings", "icon": "📊", "description": "Text embeddings"},
    "tts": {"name": "TTS", "icon": "🎙️", "description": "Text to speech"},
    "translation": {"name": "Translation", "icon": "🔤", "description": "Language translation"},
}

# ============== MODEL RANKINGS BY CATEGORY ==============
MODEL_RANKINGS = {
    "reasoning": [
        "deepseek-ai/deepseek-v3.2",        # VERIFIED WORKING
        "moonshotai/kimi-k2-instruct",      # VERIFIED WORKING
        "qwen/qwq-32b",                     # VERIFIED WORKING
        "deepseek-ai/deepseek-v3.1",
        "deepseek-r1-distill-llama-70b",    # Groq
    ],
    "coding": [
        "mistralai/devstral-2-123b-instruct-2512",  # VERIFIED WORKING
        "qwen/qwen3-coder-480b-a35b-instruct",      # VERIFIED WORKING
        "qwen/qwen2.5-coder-7b-instruct",           # VERIFIED WORKING
        "mistralai/mamba-codestral-7b-v0.1",         # VERIFIED WORKING
    ],
    "vision": [
        "google/gemma-3-27b-it",            # VERIFIED WORKING
        "meta/llama-4-maverick-17b-128e-instruct",  # VERIFIED WORKING
        "microsoft/phi-3.5-vision-instruct",
        "google/google-paligemma",
        "google/gemma-2-27b-it",
        "nvidia/internvl2-14b",
        "llama-3.2-90b-vision-preview",     # Groq
        "llama-3.2-11b-vision-preview",     # Groq
        "llava-1.5-7b-4096-preview",        # Groq
    ],
    "chat": [
        "mistralai/mistral-large-3-675b-instruct-2512",  # VERIFIED WORKING
        "mistralai/mistral-small-3.1-24b-instruct-2503", # VERIFIED WORKING
        "mistralai/mistral-medium-3-instruct",            # VERIFIED WORKING
        "microsoft/phi-3.5-mini-instruct",                 # VERIFIED WORKING
        "mistralai/mistral-7b-instruct-v0.2",             # VERIFIED WORKING
        "google/gemma-7b",                                 # VERIFIED WORKING
        "nvidia/nemotron-4-mini-hindi-4b-instruct",       # VERIFIED WORKING
        "qwen/qwen2-7b-instruct",
        "llama-3.3-70b-versatile",      # Groq
        "llama-3.1-8b-instant",         # Groq
        "mixtral-8x7b-32768",           # Groq
    ],
    "tool_calling": [
        "mistralai/mistral-nemotron",
        "moonshotai/kimi-k2-instruct",
    ],
    "agentic": [
        "stepfun-ai/step-3.5-flash",
        "bytedance/seed-oss-36b-instruct",
        "moonshotai/kimi-k2-thinking",
    ],
    "long_context": [
        "moonshotai/kimi-k2-instruct-0905",
        "deepseek-ai/deepseek-v3.2",
        "mistralai/devstral-2-123b-instruct-2512",
        "qwen/qwen3-coder-480b-a35b-instruct",
    ],
    "multilingual": [
        "nvidia/nemotron-4-mini-hindi-4b-instruct",  # VERIFIED WORKING
        "microsoft/phi-3.5-mini-instruct",
        "thudm/chatglm3-6b",
        "baichuan-inc/baichuan2-13b-chat",
        "qwen/qwen2-7b-instruct",
        "qwen/qwen3-32b",  # Groq
    ],
    "safety": [
        "meta/llama-guard-4-12b",
        "ibm/granite-guardian-3.0-8b",
        "nvidia/nemotron-content-safety-reasoning-4b",
    ],
    "embeddings": [
        "nvidia/nv-embed-v1",
        "nvidia/nv-embedcode-7b-v1",
    ],
    "tts": [
        "nvidia/magpie-tts-flow",
        "nvidia/magpie-tts-zeroshot",
    ],
    "translation": [
        "nvidia/riva-translate-4b-instruct-v1_1",
        "thudm/chatglm3-6b",
        "baichuan-inc/baichuan2-13b-chat",
    ],
}

# ============== DEFAULT BEHAVIOR ==============
DEFAULT_BEHAVIOR = {
    "name": "Saurabh AI",
    "personality": "helpful, friendly, intelligent",
    "style": "Be helpful and informative. Answer in Hinglish. Be like a senior friend.",
    "language": "Hinglish",
    "emoji_free": False
}

# ============== API FUNCTIONS ==============
async def get_next_groq_key() -> Optional[str]:
    if not GROQ_KEYS:
        return None
    
    async with current_groq_index["lock"]:
        idx = current_groq_index["index"]
        current_groq_index["index"] = (current_groq_index["index"] + 1) % len(GROQ_KEYS)
        return GROQ_KEYS[idx]

async def get_next_nvidia_key() -> Optional[str]:
    if not NVIDIA_KEYS:
        return None
    
    async with current_nvidia_index["lock"]:
        idx = current_nvidia_index["index"]
        current_nvidia_index["index"] = (current_nvidia_index["index"] + 1) % len(NVIDIA_KEYS)
        return NVIDIA_KEYS[idx]

async def stream_from_groq(api_key: str, model: str, messages: list, stream: bool = True):
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
                    yield f"data: {{\"error\": \"Groq Error: {response.status_code}\"}}\n\n".encode()
                    return
                
                async for line in response.aiter_lines():
                    if line.strip():
                        yield f"{line}\n".encode()
        except Exception as e:
            yield f"data: {{\"error\": \"Groq Connection: {str(e)}\"}}\n\n".encode()

async def stream_from_nvidia(api_key: str, model: str, messages: list, stream: bool = True):
    import time
    url = f"{NVIDIA_BASE_URL}/chat/completions"
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
    
    start_time = time.time()
    print(f"[NVIDIA] Starting stream for {model}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                elapsed = time.time() - start_time
                print(f"[NVIDIA] Got response in {elapsed:.2f}s with status {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"[NVIDIA] Error {response.status_code}: {error_text[:200]}")
                    yield f"data: {{\"error\": \"NVIDIA Error: {response.status_code}\"}}\n\n".encode()
                    return
                
                line_count = 0
                async for line in response.aiter_lines():
                    if line.strip():
                        line_count += 1
                        if line_count <= 3:  # Log first few lines
                            print(f"[NVIDIA] Line {line_count}: {line[:100]}")
                        yield f"{line}\n".encode()
                
                elapsed = time.time() - start_time
                print(f"[NVIDIA] Stream completed in {elapsed:.2f}s with {line_count} lines")
                
                # If no lines received, send a fallback response
                if line_count == 0:
                    print(f"[NVIDIA] No lines received for {model}, sending fallback")
                    fallback_data = '{"id":"chatcmpl-fallback","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"Model responded but sent empty content."},"finish_reason":null}]}'
                    yield f"data: {fallback_data}\n\n".encode()
                    yield b"data: [DONE]\n\n"
                    
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[NVIDIA] Exception after {elapsed:.2f}s: {str(e)}")
            yield f"data: {{\"error\": \"NVIDIA Connection: {str(e)}\"}}\n\n".encode()

# ============== AI ANALYZER SYSTEM ==============
CATEGORY_ANALYZER_PROMPT = """You are a smart model selector. Analyze the user's message and determine the best category.

Categories:
- reasoning: Math problems, logic puzzles, analytical thinking, step-by-step analysis
- coding: Programming, scripts, debugging, code review, algorithms
- vision: Image analysis, photo descriptions, visual content, multimodal input
- chat: Casual conversation, greetings, simple questions, general chat
- tool_calling: Agent tasks, function calling, automation workflows
- agentic: Complex autonomous tasks, multi-step planning
- long_context: Summarizing large documents, books, extensive content
- multilingual: Translations between languages, multilingual content

Respond ONLY with valid JSON (no markdown, no explanation):
{
  "category": "reasoning|coding|vision|chat|tool_calling|agentic|long_context|multilingual",
  "confidence": 0.0-1.0,
  "reason": "One sentence explanation"
}"""

def analyze_message_category(message: str) -> dict:
    """Simple keyword-based category analysis"""
    message_lower = message.lower()
    
    # Coding keywords
    coding_keywords = ["code", "program", "function", "python", "javascript", "java", "c++", "html", "css", 
                      "debug", "error", "compile", "syntax", "algorithm", "data structure", "api", "database",
                      "sql", "query", "script", "developer", "coding", "software", "app", "website"]
    
    # Reasoning keywords
    reasoning_keywords = ["solve", "calculate", "math", "problem", "logic", "puzzle", "equation", "proof",
                         "analyze", "explain why", "how does", "what is the reason", "calculate", "compute"]
    
    # Vision keywords (for image analysis)
    vision_keywords = ["image", "picture", "photo", "describe this image", "what do you see", "analyze image",
                      "look at", "visual", "screenshot", "upload"]
    
    # Multilingual keywords
    multilingual_keywords = ["translate", "hindi", "spanish", "french", "german", "language", "meaning",
                            "how to say", "what does", "in english", "in hindi", "in spanish"]
    
    # Check for coding
    if any(keyword in message_lower for keyword in coding_keywords):
        return {"category": "coding", "confidence": 0.8, "reason": "Coding-related keywords detected"}
    
    # Check for reasoning
    if any(keyword in message_lower for keyword in reasoning_keywords):
        return {"category": "reasoning", "confidence": 0.8, "reason": "Reasoning/math keywords detected"}
    
    # Check for vision (image analysis)
    if any(keyword in message_lower for keyword in vision_keywords):
        return {"category": "vision", "confidence": 0.7, "reason": "Image/visual keywords detected"}
    
    # Check for multilingual
    if any(keyword in message_lower for keyword in multilingual_keywords):
        return {"category": "multilingual", "confidence": 0.7, "reason": "Translation/language keywords detected"}
    
    # Default to chat for general conversation
    return {"category": "chat", "confidence": 0.9, "reason": "General conversation"}

def get_best_model_for_category(category: str, user_email: str = None) -> dict:
    """Get the best ranked model for a category"""
    rankings = MODEL_RANKINGS.get(category, MODEL_RANKINGS["chat"])
    
    if rankings:
        best_model = rankings[0]
        model_info = NVIDIA_MODELS.get(best_model, {})
        
        if not model_info:
            # Check Groq models
            groq_info = GROQ_MODEL_BEHAVIORS.get(best_model, {})
            if groq_info:
                return {
                    "model_id": best_model,
                    "name": groq_info.get("name", best_model),
                    "category": category,
                    "api": "groq",
                    "rank": 1,
                    "description": groq_info.get("description", "")
                }
        
        return {
            "model_id": best_model,
            "name": model_info.get("name", best_model),
            "category": category,
            "api": "nvidia",
            "rank": model_info.get("rank", 1),
            "description": model_info.get("description", ""),
            "runs": model_info.get("runs", "")
        }
    
    # Default fallback
    return {
        "model_id": "deepseek-ai/deepseek-v3.2",
        "name": "DeepSeek V3.2",
        "category": "reasoning",
        "api": "nvidia",
        "rank": 1,
        "description": "Best general reasoning model"
    }

# ============== STATIC FILES ==============
STATIC_PATH = os.path.join(os.path.dirname(__file__), "..")

# ============== ENDPOINTS ==============
@app.get("/")
async def root():
    index_path = os.path.join(STATIC_PATH, "index.html")
    return FileResponse(index_path)

@app.get("/auth/login-page")
async def login_page():
    login_path = os.path.join(os.path.dirname(__file__), "..", "auth", "login.html")
    return FileResponse(login_path)

@app.get("/ping")
async def ping():
    return {"pong": True}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "groq_keys": len(GROQ_KEYS),
        "nvidia_keys": len(NVIDIA_KEYS),
        "total_models": len(NVIDIA_MODELS) + len(GROQ_MODEL_BEHAVIORS),
        "version": "2.0.0"
    }

@app.get("/models")
async def get_models():
    """Return all available models organized by category"""
    models_by_category = {}
    
    for model_id, info in NVIDIA_MODELS.items():
        cat = info["category"]
        if cat not in models_by_category:
            models_by_category[cat] = []
        models_by_category[cat].append({
            "id": model_id,
            "name": info["name"],
            "rank": info["rank"],
            "runs": info["runs"],
            "description": info["description"],
            "context": info.get("context", ""),
            "api": "nvidia"
        })
    
    # Add Groq models
    for model_id, info in GROQ_MODEL_BEHAVIORS.items():
        cat = info["category"]
        if cat not in models_by_category:
            models_by_category[cat] = []
        models_by_category[cat].append({
            "id": model_id,
            "name": info["name"],
            "rank": info["rank"],
            "description": info["description"],
            "api": "groq"
        })
    
    return {
        "categories": CATEGORIES,
        "models_by_category": models_by_category,
        "total_nvidia": len(NVIDIA_MODELS),
        "total_groq": len(GROQ_MODEL_BEHAVIORS)
    }

@app.get("/categories")
async def get_categories():
    """Return all categories"""
    return {"categories": CATEGORIES}

@app.post("/analyze-message")
async def analyze_message(request: Request):
    """AI-based message analyzer for auto model selection"""
    try:
        body = await request.json()
        message = body.get("message", "")
        
        if not message:
            return {"error": "Message is required"}
        
        result = await analyze_message_category(message)
        
        # Get best model for detected category
        best_model = get_best_model_for_category(result["category"])
        
        return {
            "category": result["category"],
            "confidence": result["confidence"],
            "reason": result.get("reason", ""),
            "category_info": CATEGORIES.get(result["category"], {}),
            "suggested_model": best_model
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/auto-select-model")
async def auto_select_model(request: Request):
    """Get auto-selected model for a category"""
    try:
        body = await request.json()
        category = body.get("category", "chat")
        
        best_model = get_best_model_for_category(category)
        
        return {
            "success": True,
            "model": best_model
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat")
async def chat(request: Request):
    """Main chat endpoint with Groq + NVIDIA support"""
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
    api_type = body.get("api_type", "auto")
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")
    
    # Handle auto model selection
    if model == "auto" or model == "ai-selected":
        # Analyze message and get best model
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        if user_msg:
            analysis = analyze_message_category(user_msg)
            best = get_best_model_for_category(analysis["category"])
            model = best["model_id"]
            
            # Determine API type
            if best["api"] == "nvidia":
                api_type = "nvidia"
            else:
                api_type = "groq"
    
    # Check if NVIDIA model
    is_nvidia_model = any(
        model.startswith(prefix) 
        for prefix in ["deepseek-ai/", "moonshotai/", "z-ai/", "mistralai/", "qwen/", "google/", "microsoft/", "meta/", "nvidia/", "ibm/", "tiiuae/", "thudm/", "baichuan-", "openai/", "stepfun-", "bytedance/", "upstage/", "speakleash/", "aisingapore/", "rakuten/", "mediatek/", "ai21labs/"]
    )
    
    # Route to appropriate API
    if api_type == "nvidia" or is_nvidia_model:
        api_key = await get_next_nvidia_key()
        if not api_key:
            raise HTTPException(status_code=500, detail="No NVIDIA API key available")
        return StreamingResponse(
            stream_from_nvidia(api_key, model, messages),
            media_type="text/event-stream"
        )
    else:
        api_key = await get_next_groq_key()
        if not api_key:
            raise HTTPException(status_code=500, detail="No GROQ API key available")
        return StreamingResponse(
            stream_from_groq(api_key, model, messages),
            media_type="text/event-stream"
        )

@app.get("/generate-image")
async def generate_image_endpoint(prompt: str, width: int = 1024, height: int = 1024, model: str = "flux"):
    """Generate image using Pollinations AI"""
    encoded_prompt = quote(prompt)
    image_url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true"
    
    return {
        "status": "success",
        "url": image_url,
        "prompt": prompt,
        "width": width,
        "height": height,
        "model": model
    }

# ============== AUTH ENDPOINTS ==============
@app.post("/auth/login")
async def login(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE gmail = ?", (email,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=401, detail="User not found. Please register first.")
        
        if not verify_password(password, result[0]):
            conn.close()
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        cursor.execute("UPDATE users SET last_login = ?, login_count = login_count + 1 WHERE gmail = ?",
                       (datetime.now().isoformat(), email))
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
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT gmail FROM users WHERE gmail = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="User already exists")
        
        cursor.execute("INSERT INTO users (gmail, password_hash, created_at, login_count) VALUES (?, ?, ?, ?)",
                      (email, password_hash, datetime.now().isoformat(), 1))
        conn.commit()
        conn.close()
        
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

@app.get("/auth/user-info")
async def get_user_info(authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization required")
        
        token = authorization.replace("Bearer ", "")
        email = verify_jwt_token(token)
        
        if not email:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gmail, created_at, last_login, login_count FROM users WHERE gmail = ?", (email,))
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

@app.get("/auth/check-session")
async def check_session(authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return {"valid": False}
        
        token = authorization.replace("Bearer ", "")
        email = verify_jwt_token(token)
        
        return {"valid": bool(email), "email": email}
    except:
        return {"valid": False}

# ============== STARTUP ==============
@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("[SAURABH AI] Backend v2.0.0 Started!")
    print("=" * 60)
    print(f"[CONFIG] GROQ Keys: {len(GROQ_KEYS)}")
    print(f"[CONFIG] NVIDIA Keys: {len(NVIDIA_KEYS)}")
    print(f"[CONFIG] NVIDIA Models: {len(NVIDIA_MODELS)}")
    print(f"[CONFIG] GROQ Models: {len(GROQ_MODEL_BEHAVIORS)}")
    print(f"[CONFIG] Total Models: {len(NVIDIA_MODELS) + len(GROQ_MODEL_BEHAVIORS)}")
    print(f"[CONFIG] Categories: {len(CATEGORIES)}")
    print("=" * 60)

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
app.mount("/js", StaticFiles(directory=STATIC_PATH + "/js"), name="js")
app.mount("/css", StaticFiles(directory=STATIC_PATH + "/css"), name="css")

@app.get("/memory_system.js")
async def serve_memory():
    path = os.path.join(STATIC_PATH, "memory_system.js")
    return FileResponse(path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
