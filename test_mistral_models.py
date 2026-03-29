import asyncio
import httpx
import json

async def test_nvidia_model(model_id, model_name):
    """Test a specific NVIDIA model with streaming"""
    print(f"\nTesting {model_name} ({model_id})...")
    
    try:
        with open("C:/Users/hp/saurabh-ai/config/api_keys.json") as f:
            keys = json.load(f)
        
        nvidia_key = keys['nvidia_keys'][0]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test with streaming
            print(f"  Testing with streaming...")
            async with client.stream(
                "POST",
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Hello, say 'test' only. Don't write anything else."}],
                    "max_tokens": 20,
                    "temperature": 0.1,
                    "stream": True
                },
                timeout=30.0
            ) as response:
                print(f"  Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"  Error: {error_text[:300]}")
                    return False
                
                # Read streaming response
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(data)
                                content = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                full_response += content
                            except:
                                pass
                
                print(f"  Streamed response: '{full_response}'")
                return True
                
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("TESTING MISTRAL & VISION NVIDIA MODELS")
    print("=" * 60)
    
    # Models reported as failing
    nvidia_models = [
        ("mistralai/mistral-medium-3-instruct", "Mistral Medium 3"),
        ("mistralai/mistral-small-3.1-24b-instruct-2503", "Mistral Small 3.1"),
        ("mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
        ("nvidia/internvl2-14b", "InternVL2 14B"),
        ("google/google-paligemma", "PaliGemma"),
    ]
    
    results = {}
    
    print("\nTesting models with streaming:")
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
        status = "WORKING" if result["success"] else "FAILED"
        print(f"{model_name} ({result['model_id']}): {status}")
        
        if result["success"]:
            working.append(model_name)
        else:
            failed.append(model_name)
    
    print(f"\nWorking: {len(working)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(main())