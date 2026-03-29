import asyncio
import httpx
import json

async def test_groq_model(model_id, model_name):
    """Test a specific GROQ model"""
    print(f"\nTesting {model_name} ({model_id})...")
    
    try:
        with open("C:/Users/hp/saurabh-ai/config/api_keys.json") as f:
            keys = json.load(f)
        
        groq_key = keys['groq_keys'][0]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Hello, say 'test' only. Don't write anything else."}],
                    "max_tokens": 20,
                    "temperature": 0.1
                },
                timeout=30.0
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  Response: '{content}'")
                return True
            else:
                print(f"  Error: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return False

async def test_nvidia_model(model_id, model_name):
    """Test a specific NVIDIA model"""
    print(f"\nTesting {model_name} ({model_id})...")
    
    try:
        with open("C:/Users/hp/saurabh-ai/config/api_keys.json") as f:
            keys = json.load(f)
        
        nvidia_key = keys['nvidia_keys'][0]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Hello, say 'test' only. Don't write anything else."}],
                    "max_tokens": 20,
                    "temperature": 0.1
                },
                timeout=30.0
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  Response: '{content}'")
                return True
            else:
                print(f"  Error: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("TESTING SPECIFIC MODELS")
    print("=" * 60)
    
    # Models to test (Updated with working models)
    groq_models = [
        ("llama-3.3-70b-versatile", "Sage - Llama 3.3 70B"),
        ("qwen/qwen3-32b", "Poly - Qwen 3 32B"),
        ("llama-3.1-8b-instant", "Quick - Llama 3.1 8B"),
        ("meta-llama/llama-4-scout-17b-16e-instruct", "Scout - Llama 4 Vision"),
        ("moonshotai/kimi-k2-instruct", "Kimi K2"),
        ("moonshotai/kimi-k2-instruct-0905", "Kimi K2 Long"),
        ("openai/gpt-oss-120b", "GPT-OSS"),
        ("groq/compound", "Compound"),
    ]
    
    nvidia_models = [
        ("mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
        ("mistralai/devstral-2-123b-instruct-2512", "Devstral 123B"),
    ]
    
    results = {}
    
    print("\n1. Testing GROQ Models:")
    for model_id, model_name in groq_models:
        success = await test_groq_model(model_id, model_name)
        results[model_name] = {"type": "GROQ", "success": success}
        await asyncio.sleep(1)
    
    print("\n2. Testing NVIDIA Models:")
    for model_id, model_name in nvidia_models:
        success = await test_nvidia_model(model_id, model_name)
        results[model_name] = {"type": "NVIDIA", "success": success}
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = []
    failed = []
    
    for model_name, result in results.items():
        status = "WORKING" if result["success"] else "FAILED"
        print(f"{model_name} ({result['type']}): {status}")
        
        if result["success"]:
            working.append(model_name)
        else:
            failed.append(model_name)
    
    print(f"\nWorking: {len(working)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed models need attention:")
        for model in failed:
            print(f"  - {model}")

if __name__ == "__main__":
    asyncio.run(main())