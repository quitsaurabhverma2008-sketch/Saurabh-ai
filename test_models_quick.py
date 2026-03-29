import asyncio
import httpx
import json

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

with open("C:/Users/hp/saurabh-ai/config/api_keys.json", "r") as f:
    keys_data = json.load(f)
    nvidia_keys = keys_data.get("nvidia_keys", [])
    groq_keys = keys_data.get("groq_keys", [])

key_index = 0

def get_next_nvidia_key():
    global key_index
    if not nvidia_keys:
        return None
    key = nvidia_keys[key_index % len(nvidia_keys)]
    key_index += 1
    return key

async def test_single_model(model_id, questions, api="nvidia"):
    results = []
    for i, q in enumerate(questions):
        try:
            if api == "nvidia":
                url = f"{NVIDIA_BASE_URL}/chat/completions"
                key = get_next_nvidia_key()
            else:
                url = "https://api.groq.com/openai/v1/chat/completions"
                key = groq_keys[i % len(groq_keys)] if groq_keys else None
            
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": q}],
                "max_tokens": 300,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")[:200]
                results.append({"q": q, "a": answer, "success": True})
                print(f"[OK] Q{i+1}: {q[:40]}...")
            else:
                results.append({"q": q, "error": response.status_code, "success": False})
                print(f"[ERR] Q{i+1}: Status {response.status_code}")
        except Exception as e:
            results.append({"q": q, "error": str(e), "success": False})
            print(f"[ERR] Q{i+1}: {str(e)[:50]}")
        
        await asyncio.sleep(0.5)
    
    return results

async def main():
    models = [
        # Reasoning
        {"id": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2", "api": "nvidia", "category": "reasoning"},
        {"id": "moonshotai/kimi-k2-instruct", "name": "Kimi K2", "api": "nvidia", "category": "reasoning"},
        # Coding
        {"id": "z-ai/glm-4.7", "name": "GLM-4.7", "api": "nvidia", "category": "coding"},
        # Chat
        {"id": "mistralai/mistral-large-3-675b-instruct-2512", "name": "Mistral Large 3", "api": "nvidia", "category": "chat"},
        {"id": "llama-3.3-70b-versatile", "name": "Sage (GROQ)", "api": "groq", "category": "chat"},
        # Multilingual
        {"id": "nvidia/nemotron-4-mini-hindi-4b-instruct", "name": "Nemotron Hindi", "api": "nvidia", "category": "multilingual"},
    ]
    
    questions = {
        "reasoning": [
            "Calculate: 15 * 23 + 45",
            "What comes next: 2, 6, 12, 20, 30, ?",
            "If A > B and B > C, which is smallest?"
        ],
        "coding": [
            "Write a Python function to check palindrome",
            "What is difference between list.append() and extend()?",
            "Explain Big O of quicksort"
        ],
        "chat": [
            "What's a good breakfast for energy?",
            "Tell me about renewable energy",
            "How do I start learning programming?"
        ],
        "multilingual": [
            "Translate to Hindi: 'How are you?'",
            "Translate to Spanish: 'I want coffee'",
            "How do you say 'Thank you' in Japanese?"
        ]
    }
    
    all_results = {}
    
    for model in models:
        print(f"\n{'='*50}")
        print(f"Testing: {model['name']} ({model['api']})")
        print(f"{'='*50}")
        
        cat = model["category"]
        qs = questions.get(cat, questions["chat"])
        results = await test_single_model(model["id"], qs, model["api"])
        
        success_count = sum(1 for r in results if r.get("success"))
        all_results[model["name"]] = {
            "model_id": model["id"],
            "category": cat,
            "results": results,
            "success_rate": f"{success_count}/{len(results)}"
        }
        
        await asyncio.sleep(2)
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    for name, data in all_results.items():
        print(f"\n{name} ({data['category']}): {data['success_rate']}")
        for r in data["results"]:
            if r.get("success"):
                print(f"  [OK] {r['q'][:45]}...")
                print(f"      -> {r['a'][:100]}...")
            else:
                print(f"  [ERR] {r['q'][:45]}... -> {r.get('error')}")
    
    with open("C:/Users/hp/saurabh-ai/test_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n\nResults saved!")

if __name__ == "__main__":
    asyncio.run(main())
