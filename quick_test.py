from playwright.sync_api import sync_playwright

print("Starting Playwright test...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Opening app...")
    page.goto("http://localhost:3000")
    page.wait_for_timeout(3000)
    
    title = page.title()
    print(f"Page title: {title}")
    
    # Check for input
    try:
        page.fill("#msgInput", "Hi")
        print("[OK] Input field works")
    except:
        print("[FAIL] Input field not found")
    
    # Check for send button
    try:
        page.click("#sendBtn")
        print("[OK] Send button works")
        page.wait_for_timeout(5000)
    except:
        print("[FAIL] Send button not found")
    
    browser.close()
    print("Test complete!")
