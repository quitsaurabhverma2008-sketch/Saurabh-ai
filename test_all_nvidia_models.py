import asyncio
import httpx
import json

async def test_nvidia_model(model_id, model_name):
    """Test a specific NVIDIA model"""
    print(f"\nTesting {model_name}...")
    
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
    print("TESTING ALL REPORTED FAILING NVIDIA MODELS")
    print("=" * 60)
    
    # All models reported as failing
    nvidia_models = [
        ("nvidia/cosmos-nemotron-34b", "Cosmos Nemotron"),
        ("qwen/qwen2.5-coder-7b-instruct", "Qwen2.5 Coder 7B"),
        ("mistralai/devstral-2-123b-instruct-2512", "Devstral 123B"),
        ("marin/marin-8b-instruct", "Marin 8B"),
        ("deepseek-ai/deepseek-r1", "DeepSeek R1"),
        ("qwen/qwq-32b", "QwQ-32B"),
        # Also test Mistral models
        ("mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
        ("mistralai/mistral-medium-3-instruct", "Mistral Medium 3"),
        ("mistralai/mistral-small-3.1-24b-instruct-2503", "Mistral Small 3.1"),
    ]
    
    results = {}
    
    print("\nTesting models:")
    for model_id, model_name in nvidia_models:
        success = await test_nvidia_model(model_id, model_name)
        results[model_name] = {"model_id": model_id, "success": success}
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = []
    failed = []
    
    for model_name, result in results.items():
        status = "✅ WORKING" if result["success"] else "❌ FAILED"
        print(f"{model_name}: {status}")
        
        if result["success"]:
            working.append(model_name)
        else:
            failed.append(model_name)
    
    print(f"\nWorking: {len(working)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    
    if failed:
        print("\nModels that need attention:")
        for model in failed:
            print(f"  - {model}")

if __name__ == "__main__":
    asyncio.run(main())