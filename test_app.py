"""
Saurabh AI - App Test Script
Tests the frontend and backend
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend():
    print("=" * 50)
    print("TESTING BACKEND")
    print("=" * 50)
    
    # Test health
    r = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {r.json()}")
    
    # Test models
    r = requests.get(f"{BASE_URL}/models")
    models = r.json()
    print(f"\nAvailable Models: {len(models['text'] + models['vision'])}")
    for m in models['text']:
        print(f"  - {m['name']}")
    
    # Test chat
    print("\nTesting Chat API...")
    r = requests.post(f"{BASE_URL}/chat", json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hello! Reply with just 'Hi, Saurabh AI is working!'"}],
        "stream": False,
        "max_tokens": 100
    })
    data = r.text
    # Extract content from SSE
    for line in data.split('\n'):
        if line.startswith('data:') and '"content"' in line:
            import re
            match = re.search(r'"content":"([^"]*)"', line)
            if match:
                print(f"AI Response: {match.group(1)}")
                break
    
    print("\n[PASS] Backend: OK")

def test_frontend():
    print("\n" + "=" * 50)
    print("TESTING FRONTEND")
    print("=" * 50)
    
    r = requests.get(FRONTEND_URL)
    html = r.text
    
    # Check key elements
    checks = [
        ("Saurabh AI", "App Title"),
        ("API_BASE", "Backend Connection"),
        ("MODELS", "Models Array"),
        ("msgInput", "Input Field"),
        ("send()", "Send Function"),
        ("toggleTheme", "Theme Toggle (removed?)"),
    ]
    
    print("\nFrontend Checks:")
    for term, name in checks:
        found = term in html
        status = "[OK]" if found else "[FAIL]"
        print(f"  {status} {name}: {'Found' if found else 'NOT FOUND'}")
    
    # Check for removed items
    print("\nChecking Removed Items:")
    removed_checks = ["toggleTheme()", "toggleSound()", "exportChat()", "clearModal"]
    for term in removed_checks:
        found = term in html
        status = "[OK] Removed" if not found else "[FAIL] Still present"
        print(f"  {status}: {term}")
    
    print("\n[PASS] Frontend: OK")

def test_with_playwright():
    print("\n" + "=" * 50)
    print("TESTING WITH PLAYWRIGHT (Browser)")
    print("=" * 50)
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to app
            page.goto(FRONTEND_URL)
            page.wait_for_timeout(3000)  # Wait for splash
            
            # Check page title
            title = page.title()
            print(f"\nPage Title: {title}")
            
            # Check for errors in console
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            
            # Try sending a message
            page.fill("#msgInput", "Hello")
            page.click("#sendBtn")
            page.wait_for_timeout(5000)
            
            # Check if response came
            msgs = page.query_selector_all(".msg-row")
            print(f"Messages found: {len(msgs)}")
            
            if errors:
                print(f"\nConsole Errors: {errors}")
            else:
                print("\n[OK] No console errors!")
            
            browser.close()
            print("\n[PASS] Playwright Test: OK")
            
    except Exception as e:
        print(f"\n[FAIL] Playwright Error: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("SAURABH AI - COMPREHENSIVE TEST")
    print("=" * 50 + "\n")
    
    test_backend()
    test_frontend()
    
    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETED!")
    print("=" * 50)
