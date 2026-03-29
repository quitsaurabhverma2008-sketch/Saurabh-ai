import json
import httpx
import asyncio
import sys
import traceback

async def test_nvidia_key():
    """Test a single NVIDIA API key"""
    try:
        # Load config
        with open("C:/Users/hp/saurabh-ai/config/api_keys.json", "r") as f:
            config = json.load(f)
        
        nvidia_keys = config.get("nvidia_keys", [])
        
        if not nvidia_keys:
            print("ERROR: No NVIDIA API keys found in config")
            return False
        
        print(f"Found {len(nvidia_keys)} NVIDIA API keys")
        print(f"Testing first key: {nvidia_keys[0][:30]}...")
        
        # Test with Mistral Large 3 (should be more reliable)
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {nvidia_keys[0]}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistralai/mistral-large-3-675b-instruct-2512",
            "messages": [{"role": "user", "content": "Hello, respond with 'Hi there' only."}],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        print(f"\nTesting with model: mistralai/mistral-large-3-675b-instruct-2512")
        print(f"URL: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: NVIDIA API key is working!")
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"Response: {content}")
                return True
            elif response.status_code == 401:
                print("FAILED: NVIDIA API key is INVALID (401 Unauthorized)")
                print("Error details:", response.text[:300])
                return False
            elif response.status_code == 403:
                print("FAILED: NVIDIA API key is FORBIDDEN (403)")
                print("Error details:", response.text[:300])
                return False
            elif response.status_code == 404:
                print("FAILED: Model not found (404)")
                print("Trying with a different model...")
                # Try with a different model
                payload["model"] = "mistralai/mistral-small-3.1-24b-instruct-2503"
                response2 = await client.post(url, headers=headers, json=payload)
                print(f"Second model response: {response2.status_code}")
                if response2.status_code == 200:
                    print("SUCCESS: Different model works! Model ID might be wrong.")
                    return True
                else:
                    print("FAILED: Different model also failed")
                    return False
            else:
                print(f"FAILED: Unexpected status code: {response.status_code}")
                print("Error details:", response.text[:300])
                return False
                
    except Exception as e:
        print(f"ERROR testing NVIDIA: {str(e)}")
        traceback.print_exc()
        return False

async def test_groq_key():
    """Test a single GROQ API key"""
    try:
        # Load config
        with open("C:/Users/hp/saurabh-ai/config/api_keys.json", "r") as f:
            config = json.load(f)
        
        groq_keys = config.get("groq_keys", [])
        
        if not groq_keys:
            print("\nERROR: No GROQ API keys found in config")
            return False
        
        print(f"\nFound {len(groq_keys)} GROQ API keys")
        print(f"Testing first key: {groq_keys[0][:30]}...")
        
        # Test with Llama 3.3 70B
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_keys[0]}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Hello, respond with 'Hi there' only."}],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        print(f"\nTesting with model: llama-3.3-70b-versatile")
        print(f"URL: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: GROQ API key is working!")
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"Response: {content}")
                return True
            elif response.status_code == 401:
                print("FAILED: GROQ API key is INVALID (401 Unauthorized)")
                print("Error details:", response.text[:300])
                return False
            else:
                print(f"FAILED: GROQ API returned status: {response.status_code}")
                print("Error details:", response.text[:300])
                return False
                
    except Exception as e:
        print(f"ERROR testing GROQ: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("NVIDIA & GROQ API KEY VALIDATION TEST")
    print("=" * 60)
    
    nvidia_ok = await test_nvidia_key()
    groq_ok = await test_groq_key()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"NVIDIA API: {'WORKING' if nvidia_ok else 'FAILED'}")
    print(f"GROQ API: {'WORKING' if groq_ok else 'FAILED'}")
    
    if not nvidia_ok and not groq_ok:
        print("\nWARNING: BOTH APIs FAILED - Check API keys or network connection")
        print("Possible issues:")
        print("1. API keys are expired/invalid")
        print("2. Network/firewall blocking API calls")
        print("3. API rate limits exceeded")
        print("4. Wrong API endpoint URLs")
    elif nvidia_ok or groq_ok:
        print("\nSUCCESS: At least one API is working!")
        print("We can proceed with fixing the other API.")

if __name__ == "__main__":
    asyncio.run(main())