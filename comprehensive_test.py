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

# Test questions for each category
QUESTIONS = {
    "reasoning": [
        "Calculate: 15 * 23 + 45 = ?",
        "What comes next: 2, 6, 12, 20, 30, ?",
        "If A > B and B > C, which is smallest?"
    ],
    "coding": [
        "Write a Python function to check palindrome",
        "What is difference between append() and extend()?",
        "Explain Big O of quicksort"
    ],
    "vision": [
        "Describe what you see in a sunset photo",
        "What objects are typical in a kitchen?",
        "How does photosynthesis work?"
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
    ],
    "tool_calling": [
        "Create a function that calculates BMI",
        "Write a function to format currency",
        "Design a calculator tool"
    ],
    "agentic": [
        "Plan a trip to Goa for 3 days",
        "How would you research a new topic?",
        "Create a weekly meal plan"
    ]
}

MODELS_TO_TEST = {
    "reasoning": [
        {"id": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2", "api": "nvidia"},
        {"id": "moonshotai/kimi-k2-instruct", "name": "Kimi K2", "api": "nvidia"},
        {"id": "qwen/qwq-32b", "name": "QwQ-32B", "api": "nvidia"},
    ],
    "coding": [
        {"id": "mistralai/devstral-2-123b-instruct-2512", "name": "Devstral 123B", "api": "nvidia"},
        {"id": "qwen/qwen3-coder-480b-a35b-instruct", "name": "Qwen3 Coder", "api": "nvidia"},
        {"id": "qwen/qwen2.5-coder-7b-instruct", "name": "Qwen2.5 Coder", "api": "nvidia"},
    ],
    "chat": [
        {"id": "mistralai/mistral-large-3-675b-instruct-2512", "name": "Mistral Large 3", "api": "nvidia"},
        {"id": "mistralai/mistral-small-3.1-24b-instruct-2503", "name": "Mistral Small 3.1", "api": "nvidia"},
        {"id": "google/gemma-7b", "name": "Gemma 7B", "api": "nvidia"},
    ],
    "multilingual": [
        {"id": "nvidia/nemotron-4-mini-hindi-4b-instruct", "name": "Nemotron Hindi", "api": "nvidia"},
        {"id": "thudm/chatglm3-6b", "name": "ChatGLM3 6B", "api": "nvidia"},
    ],
    "vision": [
        {"id": "google/gemma-3-27b-it", "name": "Gemma 3 27B", "api": "nvidia"},
        {"id": "meta/llama-4-maverick-17b-128e-instruct", "name": "Llama 4 Maverick", "api": "nvidia"},
    ],
}

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
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "answer": answer[:300], "status": response.status_code}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "status": response.status_code}
            
    except Exception as e:
        return {"success": False, "error": str(e)[:100]}

async def main():
    print("=" * 70)
    print("COMPREHENSIVE MODEL TESTING")
    print("=" * 70)
    
    all_results = {}
    
    for category, models in MODELS_TO_TEST.items():
        print(f"\n{'='*70}")
        print(f"CATEGORY: {category.upper()}")
        print(f"{'='*70}")
        
        questions = QUESTIONS.get(category, QUESTIONS["chat"])
        category_results = {}
        
        for model in models:
            print(f"\n--- {model['name']} ---")
            model_results = []
            
            for i, question in enumerate(questions):
                result = await test_model(model["id"], question, model["api"])
                model_results.append({
                    "question": question,
                    "result": result
                })
                
                if result.get("success"):
                    answer_preview = result["answer"][:80].replace("\n", " ")
                    print(f"  Q{i+1}: [OK] {answer_preview}...")
                else:
                    print(f"  Q{i+1}: [FAIL] {result.get('error', 'Unknown error')}")
                
                await asyncio.sleep(1)
            
            success_count = sum(1 for r in model_results if r["result"].get("success"))
            category_results[model["name"]] = {
                "model_id": model["id"],
                "api": model["api"],
                "questions_answered": success_count,
                "total_questions": len(questions),
                "success_rate": f"{success_count}/{len(questions)}",
                "results": model_results
            }
        
        all_results[category] = category_results
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for category, models in all_results.items():
        print(f"\n{category.upper()}:")
        for name, data in models.items():
            status = "PASS" if data["questions_answered"] == data["total_questions"] else "PARTIAL" if data["questions_answered"] > 0 else "FAIL"
            print(f"  {name}: {data['success_rate']} [{status}]")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"C:/Users/hp/saurabh-ai/model_test_results_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
