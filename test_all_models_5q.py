import asyncio
import httpx
import json
from datetime import datetime

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

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

def get_next_groq_key():
    global key_index
    if not groq_keys:
        return None
    key = groq_keys[key_index % len(groq_keys)]
    key_index += 1
    return key

# Test questions by category (5 questions each)
QUESTIONS = {
    "reasoning": [
        "If all cats are animals and some animals are black, can we conclude some cats are black?",
        "Calculate: 25 * 17 + 83 = ?",
        "What comes next: 3, 6, 11, 18, 27, ?",
        "A train leaves at 10 AM traveling 60 km/h. Another leaves at 11 AM traveling 80 km/h. When will they meet?",
        "If 5 machines make 5 widgets in 5 minutes, how long for 100 machines to make 100 widgets?"
    ],
    "coding": [
        "Write a Python function to reverse a string",
        "What is the difference between list and tuple in Python?",
        "Explain Big O notation of bubble sort",
        "Write JavaScript code to debounce a function",
        "What is a closure in JavaScript?"
    ],
    "vision": [
        "Describe what you see in a sunset photo",
        "What objects are typically found in a kitchen?",
        "Describe the emotion in a rainy day photo",
        "What animals might you see on a farm?",
        "Describe a typical beach scene"
    ],
    "chat": [
        "What's a good dinner recipe?",
        "Tell me about space exploration",
        "How does exercise benefit health?",
        "Suggest a weekend activity",
        "Explain how computers work"
    ],
    "multilingual": [
        "Translate to Hindi: 'Good morning'",
        "Translate to Spanish: 'I love you'",
        "How do you say 'Thank you' in Japanese?",
        "Translate to French: 'Where is the bathroom?'",
        "How do you say 'Happy birthday' in German?"
    ],
    "tool_calling": [
        "Create a function that calculates area of a circle",
        "Write a function to format a date",
        "Design a function that validates an email",
        "Create a function to get current timestamp",
        "Write a function to generate random password"
    ],
    "agentic": [
        "Plan a weekend trip to a hill station",
        "How would you organize a study schedule?",
        "Create a daily routine for productivity",
        "Plan a birthday party for a child",
        "Design a home exercise routine"
    ]
}

MODELS_TO_TEST = [
    # Reasoning
    {"id": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2", "api": "nvidia", "category": "reasoning"},
    {"id": "moonshotai/kimi-k2-instruct", "name": "Kimi K2", "api": "nvidia", "category": "reasoning"},
    {"id": "qwen/qwq-32b", "name": "QwQ-32B", "api": "nvidia", "category": "reasoning"},
    
    # Coding
    {"id": "mistralai/devstral-2-123b-instruct-2512", "name": "Devstral 123B", "api": "nvidia", "category": "coding"},
    {"id": "qwen/qwen3-coder-480b-a35b-instruct", "name": "Qwen3 Coder", "api": "nvidia", "category": "coding"},
    {"id": "qwen/qwen2.5-coder-7b-instruct", "name": "Qwen2.5 Coder", "api": "nvidia", "category": "coding"},
    
    # Vision
    {"id": "google/gemma-3-27b-it", "name": "Gemma 3 27B", "api": "nvidia", "category": "vision"},
    {"id": "meta/llama-4-maverick-17b-128e-instruct", "name": "Llama 4 Maverick", "api": "nvidia", "category": "vision"},
    
    # Chat
    {"id": "mistralai/mistral-large-3-675b-instruct-2512", "name": "Mistral Large 3", "api": "nvidia", "category": "chat"},
    {"id": "mistralai/mistral-small-3.1-24b-instruct-2503", "name": "Mistral Small 3.1", "api": "nvidia", "category": "chat"},
    {"id": "google/gemma-7b", "name": "Gemma 7B", "api": "nvidia", "category": "chat"},
    
    # Multilingual
    {"id": "nvidia/nemotron-4-mini-hindi-4b-instruct", "name": "Nemotron Hindi", "api": "nvidia", "category": "multilingual"},
    
    # GROQ
    {"id": "llama-3.3-70b-versatile", "name": "Sage (GROQ)", "api": "groq", "category": "chat"},
    {"id": "deepseek-r1-distill-llama-70b", "name": "Logic (GROQ)", "api": "groq", "category": "reasoning"},
]

async def test_model(model_id, question, api="nvidia"):
    try:
        if api == "nvidia":
            url = f"{NVIDIA_BASE_URL}/chat/completions"
            key = get_next_nvidia_key()
        else:
            url = f"{GROQ_BASE_URL}/chat/completions"
            key = get_next_groq_key()
        
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": question}],
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "answer": answer[:200], "time": "OK"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except asyncio.TimeoutError:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)[:50]}

async def main():
    print("=" * 80)
    print("COMPREHENSIVE MODEL TESTING - 5 Questions Each Model")
    print("=" * 80)
    
    results = {}
    
    for model in MODELS_TO_TEST:
        print(f"\n{'='*80}")
        print(f"MODEL: {model['name']} ({model['api'].upper()}) - {model['category'].upper()}")
        print(f"{'='*80}")
        
        questions = QUESTIONS.get(model["category"], QUESTIONS["chat"])
        model_results = []
        
        for i, question in enumerate(questions):
            print(f"\nQ{i+1}: {question[:60]}...")
            result = await test_model(model["id"], question, model["api"])
            model_results.append({
                "q": question,
                "result": result
            })
            
            if result.get("success"):
                answer = result["answer"][:80].replace("\n", " ")[:80]
                print(f"    -> {answer}...")
            else:
                print(f"    -> ERROR: {result.get('error')}")
            
            await asyncio.sleep(1)
        
        success_count = sum(1 for r in model_results if r["result"].get("success"))
        results[model["name"]] = {
            "model_id": model["id"],
            "api": model["api"],
            "category": model["category"],
            "passed": success_count,
            "total": len(questions),
            "results": model_results
        }
        
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    for name, data in results.items():
        status = "PASS" if data["passed"] == data["total"] else "PARTIAL" if data["passed"] > 0 else "FAIL"
        print(f"{name} ({data['api']}, {data['category']}): {data['passed']}/{data['total']} [{status}]")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"C:/Users/hp/saurabh-ai/model_test_5q_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
