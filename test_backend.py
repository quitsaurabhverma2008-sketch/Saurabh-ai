import asyncio
import httpx
import json
import sys

async def test_backend():
    """Test the backend server"""
    base_url = "http://localhost:8000"
    
    print("Testing Saurabh AI Backend...")
    
    try:
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            print("\n1. Testing health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"SUCCESS: Health check passed - {health}")
            else:
                print(f"FAILED: Health check failed - {response.status_code}")
                return False
            
            # Test models endpoint
            print("\n2. Testing models endpoint...")
            response = await client.get(f"{base_url}/models")
            if response.status_code == 200:
                models = response.json()
                print(f"SUCCESS: Models endpoint working - Total models: {models.get('total_nvidia', 0) + models.get('total_groq', 0)}")
            else:
                print(f"FAILED: Models endpoint failed - {response.status_code}")
                return False
            
            # Test chat with a simple message (need auth token)
            print("\n3. Testing chat endpoint (requires auth)...")
            print("Note: Chat endpoint requires authentication token")
            
            print("\nSUCCESS: Basic backend tests passed!")
            print("The backend appears to be running correctly.")
            return True
            
    except Exception as e:
        print(f"ERROR: Testing backend - {e}")
        print("\nMake sure the backend server is running:")
        print("cd 'C:\\Users\\hp\\saurabh-ai' && python backend/server.py")
        return False

if __name__ == "__main__":
    asyncio.run(test_backend())