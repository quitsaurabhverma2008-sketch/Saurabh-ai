"""
Saurabh AI - Pytest Test Suite
Run with: pytest test_suite.py -v
"""
import pytest
import requests
import time
import re

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class TestBackend:
    """Backend API Tests"""
    
    def test_health_check(self):
        """Test backend health endpoint"""
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["groq_keys_total"] == 10
        assert data["groq_keys_active"] == 10
    
    def test_models_endpoint(self):
        """Test models list endpoint"""
        r = requests.get(f"{BASE_URL}/models")
        assert r.status_code == 200
        data = r.json()
        assert "text" in data
        assert "vision" in data
        assert len(data["text"]) >= 5  # At least 5 text models
        assert len(data["vision"]) >= 2  # At least 2 vision models
    
    def test_chat_non_streaming(self):
        """Test chat endpoint with non-streaming response"""
        r = requests.post(f"{BASE_URL}/chat", json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Say 'OK' only"}],
            "stream": False,
            "max_tokens": 50
        })
        assert r.status_code == 200
        # Check response contains content
        assert "content" in r.text or "OK" in r.text

class TestFrontend:
    """Frontend Tests"""
    
    def test_frontend_accessible(self):
        """Test frontend is accessible"""
        r = requests.get(FRONTEND_URL)
        assert r.status_code == 200
        assert "Saurabh AI" in r.text
    
    def test_frontend_has_required_elements(self):
        """Test frontend has all required elements"""
        r = requests.get(FRONTEND_URL)
        html = r.text
        
        # Check key elements exist
        assert 'id="msgInput"' in html, "Input field missing"
        assert 'id="sendBtn"' in html, "Send button missing"
        assert 'id="chatsList"' in html, "Chat list missing"
        assert 'id="chatArea"' in html, "Chat area missing"
    
    def test_removed_features(self):
        """Verify removed features are actually removed"""
        r = requests.get(FRONTEND_URL)
        html = r.text
        
        # These should NOT exist
        assert "toggleTheme()" not in html, "toggleTheme still present"
        assert "toggleSound()" not in html, "toggleSound still present"
        assert "exportChat()" not in html, "exportChat still present"
        assert 'id="clearModal"' not in html, "clearModal still present"
    
    def test_models_defined(self):
        """Test that models array is properly defined"""
        r = requests.get(FRONTEND_URL)
        html = r.text
        
        # Check for key models
        assert "llama-3.3-70b-versatile" in html, "Llama 3.3 missing"
        assert "deepseek-r1-distill-llama-70b" in html, "DeepSeek R1 missing"
        assert "llama-3.2-90b-vision-preview" in html, "Vision model missing"

class TestIntegration:
    """Integration Tests"""
    
    def test_backend_and_frontend_running(self):
        """Verify both servers are running"""
        backend = requests.get(f"{BASE_URL}/health")
        frontend = requests.get(FRONTEND_URL)
        
        assert backend.status_code == 200, "Backend not running"
        assert frontend.status_code == 200, "Frontend not running"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
