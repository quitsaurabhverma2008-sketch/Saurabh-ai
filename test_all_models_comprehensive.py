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
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  WORKING: '{content[:50]}'")
                return True
            else:
                print(f"  FAILED: Status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  EXCEPTION: {str(e)[:100]}")
        return False

async def main():
    print("=" * 60)
    print("TESTING ALL REPORTED FAILING MODELS")
    print("=" * 60)
    
    # All models reported as failing
    nvidia_models = [
        ("baichuan-inc/baichuan2-13b-chat", "Baichuan 2 13B"),
        ("mistralai/devstral-2-123b-instruct-2512", "Devstral 123B"),
        ("mistralai/mistral-7b-instruct-v0.2", "Mistral 7B"),
        ("google/gemma-7b", "Gemma 7B"),
        ("mediatek/breeze-7b-instruct", "Breeze 7B"),
        ("rakuten/rakutenai-7b-chat", "RakutenAI 7B"),
        ("mistralai/mistral-nemotron", "Mistral Nemotron"),
        ("mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
        ("mistralai/mistral-small-3.1-24b-instruct-2503", "Mistral Small 3.1"),
        ("mistralai/mistral-medium-3-instruct", "Mistral Medium 3"),
        ("qwen/qwen2.5-coder-7b-instruct", "Qwen2.5 Coder 7B"),
        ("mistralai/mamba-codestral-7b-v0.1", "Codestral 7B"),
        ("google/gemma-3-27b-it", "Gemma 3 27B"),
        ("marin/marin-8b-instruct", "Marin 8B"),
    ]
    
    results = {}
    
    print("\nTesting models:")
    for model_id, model_name in nvidia_models:
        success = await test_nvidia_model(model_id, model_name)
        results[model_name] = {"model_id": model_id, "success": success}
        await asyncio.sleep(0.5)  # Small delay to avoid rate limits
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = []
    failed = []
    
    for model_name, result in results.items():
        if result["success"]:
            print(f"[WORKING] {model_name}")
            working.append(model_name)
        else:
            print(f"[FAILED] {model_name}")
            failed.append(model_name)
    
    print(f"\nWorking: {len(working)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    
    # Save results to file
    with open("model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to model_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())