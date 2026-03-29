import asyncio
import httpx
import json
from datetime import datetime

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

with open("C:/Users/hp/saurabh-ai/config/api_keys.json", "r") as f:
    keys_data = json.load(f)
    nvidia_keys = keys_data.get("nvidia_keys", [])

key_index = 0

def get_next_key():
    global key_index
    key = nvidia_keys[key_index % len(nvidia_keys)]
    key_index += 1
    return key

async def test_model(model_id, questions):
    results = []
    for q in questions:
        try:
            headers = {"Authorization": f"Bearer {get_next_key()}", "Content-Type": "application/json"}
            payload = {"model": model_id, "messages": [{"role": "user", "content": q}], "max_tokens": 200, "temperature": 0.3}
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(f"{NVIDIA_BASE_URL}/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                ans = r.json()["choices"][0]["message"]["content"][:150].replace("\n", " ")
                results.append({"q": q[:50], "a": ans, "ok": True})
            else:
                results.append({"q": q[:50], "e": r.status_code, "ok": False})
        except Exception as e:
            results.append({"q": q[:50], "e": str(e)[:30], "ok": False})
        await asyncio.sleep(0.5)
    return results

async def main():
    models = {
        "DeepSeek V3.2": ("deepseek-ai/deepseek-v3.2", [
            "Calculate: 15 * 23 + 45",
            "What comes next: 2, 6, 12, 20, 30, ?",
            "If A > B and B > C, which is smallest?",
            "Solve: 3x + 7 = 22",
            "What is 20% of 150?"
        ]),
        "Kimi K2": ("moonshotai/kimi-k2-instruct", [
            "Calculate: 25 * 17 + 83",
            "What comes next: 1, 4, 9, 16, 25, ?",
            "If today is Monday, what day after 100 days?",
            "Solve: x^2 = 64",
            "What is 50% of 200?"
        ]),
        "Devstral 123B": ("mistralai/devstral-2-123b-instruct-2512", [
            "Write a Python function to check palindrome",
            "What is difference between append and extend?",
            "Explain Big O of quicksort",
            "Write a function to find factorial",
            "What is a closure in programming?"
        ]),
        "Qwen3 Coder": ("qwen/qwen3-coder-480b-a35b-instruct", [
            "Write Python code for fibonacci",
            "What is difference between list and set?",
            "Explain recursion with example",
            "Write a function to reverse linked list",
            "What is polymorphism?"
        ]),
        "Gemma 3 27B": ("google/gemma-3-27b-it", [
            "Describe a sunset photo",
            "What objects in a kitchen?",
            "Describe a rainy day scene",
            "What animals on a farm?",
            "Describe a beach"
        ]),
        "Mistral Large 3": ("mistralai/mistral-large-3-675b-instruct-2512", [
            "What's a good breakfast?",
            "Tell me about space",
            "How does exercise help?",
            "Suggest a weekend plan",
            "Explain how computers work"
        ]),
        "Nemotron Hindi": ("nvidia/nemotron-4-mini-hindi-4b-instruct", [
            "Translate to Hindi: 'Good morning'",
            "Translate to Hindi: 'How are you?'",
            "Translate to Hindi: 'Thank you'",
            "Say hello in Hindi",
            "Translate to Hindi: 'See you later'"
        ]),
    }
    
    all_results = {}
    
    for name, (model_id, questions) in models.items():
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        results = await test_model(model_id, questions)
        all_results[name] = results
        for i, r in enumerate(results):
            if r["ok"]:
                print(f"Q{i+1}: {r['q']}... -> {r['a'][:60]}...")
            else:
                print(f"Q{i+1}: ERROR - {r.get('e')}")
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, results in all_results.items():
        passed = sum(1 for r in results if r["ok"])
        print(f"{name}: {passed}/{len(results)} passed")
    
    with open("C:/Users/hp/saurabh-ai/test_5q_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\nResults saved!")

if __name__ == "__main__":
    asyncio.run(main())
