#!/usr/bin/env python3
"""
Saurabh AI - NVIDIA Environment Variables Setup Script

This script prints the environment variables you need to add to Render Dashboard.

Usage:
    python setup_nvidia_env.py

Then copy each Key-Value pair to:
https://dashboard.render.com/web/srv-XXXXX/environment
"""

import json
import os

def main():
    # Load API keys from config file
    config_path = os.path.join(os.path.dirname(__file__), "config", "api_keys.json")
    
    print("=" * 70)
    print("SAURABH AI - NVIDIA ENVIRONMENT VARIABLES SETUP")
    print("=" * 70)
    print()
    print("Go to Render Dashboard:")
    print("https://dashboard.render.com/web/saurabh-ai/environment")
    print()
    print("Click 'Add Environment Variable' and add each key-value pair below:")
    print()
    print("=" * 70)
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("ERROR: config/api_keys.json not found!")
        print("Make sure you're running this script from the project root directory.")
        return
    
    nvidia_keys = config.get("nvidia_keys", [])
    groq_keys = config.get("groq_keys", [])
    
    print(f"\nFound: {len(groq_keys)} GROQ keys, {len(nvidia_keys)} NVIDIA keys")
    
    # Print GROQ keys (already working on Render, but showing for reference)
    print("\n" + "=" * 70)
    print("GROQ KEYS (Already working on Render - skip if already set)")
    print("=" * 70)
    for i, key in enumerate(groq_keys, 1):
        print(f"\nKey: GROQ_API_KEY_{i}")
        print(f"Value: {key}")
    
    # Print NVIDIA keys (need to be added)
    print("\n" + "=" * 70)
    print("NVIDIA KEYS (Add these to Render - REQUIRED for NVIDIA models)")
    print("=" * 70)
    for i, key in enumerate(nvidia_keys, 1):
        print(f"\nKey: NVIDIA_API_KEY_{i}")
        print(f"Value: {key}")
    
    print("\n" + "=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print("1. Go to: https://dashboard.render.com/web/saurabh-ai/environment")
    print("2. For each NVIDIA key above:")
    print("   - Click 'Add Environment Variable'")
    print("   - Copy the Key (e.g., NVIDIA_API_KEY_1)")
    print("   - Copy the Value (e.g., nvapi-xxx...)")
    print("   - Click 'Save'")
    print("3. After adding all 10 NVIDIA keys, Render will auto-redeploy")
    print("4. Wait 1-2 minutes for deployment")
    print("5. Test at: https://saurabh-ai.onrender.com")
    print()
    print("After deployment, check: https://saurabh-ai.onrender.com/health")
    print("   Should show: 'nvidia_keys': 10")
    print()

if __name__ == "__main__":
    main()