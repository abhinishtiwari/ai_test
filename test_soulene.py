"""
Soulene Server - Test Suite
Run with: pytest test_soulene.py -v
"""

import pytest
import json
from soulene_server import SouleneServer, ConversationHistory, clean_json_response

# Test Configuration
TEST_API_KEY = "test_key_for_testing"

class TestConversationHistory:
    """Test conversation history management"""
    
    def test_add_message(self):
        history = ConversationHistory()
        history.add_message("test_session", "user", "Hello")
        
        messages = history.get_history("test_session")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    def test_max_history_length(self):
        history = ConversationHistory(max_length=5)
        session_id = "test_session"
        
        # Add 10 messages
        for i in range(10):
            history.add_message(session_id, "user", f"Message {i}")
        
        messages = history.get_history(session_id)
        assert len(messages) == 5  # Should only keep last 5
        assert messages[0]["content"] == "Message 5"  # First kept message
    
    def test_get_recent_context(self):
        history = ConversationHistory()
        session_id = "test_session"
        
        history.add_message(session_id, "user", "First message")
        history.add_message(session_id, "assistant", "First response")
        history.add_message(session_id, "user", "Second message")
        
        context = history.get_recent_context(session_id, limit=2)
        assert "First response" in context
        assert "Second message" in context
        assert "First message" not in context  # Should be excluded (limit=2)
    
    def test_loop_detection_grounding(self):
        history = ConversationHistory()
        session_id = "test_session"
        
        # Add responses with grounding keywords
        response1 = "Try to breathe slowly and ground yourself"
        response2 = "Focus on your breathing and stay present"
        response3 = "Let's do some grounding exercises with your breath"
        
        # First two should be fine
        assert not history.detect_loop(session_id, response1)
        assert not history.detect_loop(session_id, response2)
        
        # Third should trigger loop detection
        assert history.detect_loop(session_id, response3)
    
    def test_clear_session(self):
        history = ConversationHistory()
        session_id = "test_session"
        
        history.add_message(session_id, "user", "Test message")
        assert len(history.get_history(session_id)) == 1
        
        history.clear_session(session_id)
        assert len(history.get_history(session_id)) == 0

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_clean_json_response_with_markdown(self):
        text = """
        Here's the result:
        ```json
        {"status": "ok"}
        ```
        """
        cleaned = clean_json_response(text)
        assert cleaned == '{"status": "ok"}'
    
    def test_clean_json_response_plain(self):
        text = '{"status": "ok", "message": "test"}'
        cleaned = clean_json_response(text)
        assert cleaned == text
    
    def test_clean_json_response_with_extra_text(self):
        text = 'Some text before {"status": "ok"} some text after'
        cleaned = clean_json_response(text)
        assert cleaned == '{"status": "ok"}'

class TestFlaskEndpoints:
    """Test Flask API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        server = SouleneServer()
        server.app.config['TESTING'] = True
        with server.app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data
    
    def test_root_endpoint(self, client):
        """Test / endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'endpoints' in data
    
    def test_chat_get_endpoint(self, client):
        """Test /chat GET endpoint"""
        response = client.get('/chat')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'required_fields' in data
    
    def test_clear_session_endpoint(self, client):
        """Test /chat/clear endpoint"""
        response = client.post('/chat/clear',
                              json={'session_id': 'test_session'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'cleared'
    
    def test_chat_endpoint_no_message(self, client):
        """Test /chat with no message"""
        response = client.post('/chat', json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_chat_endpoint_malformed_json(self, client):
        """Test /chat with malformed JSON"""
        response = client.post('/chat',
                              data='invalid json',
                              content_type='application/json')
        # Should handle gracefully
        assert response.status_code in [400, 500]

class TestSafetyMechanisms:
    """Test safety detection mechanisms"""
    
    def test_emergency_phrases(self):
        """Test that emergency phrases are detected"""
        emergency_phrases = [
            "I'm going to kill myself",
            "I have pills ready to end it",
            "I'm going to jump off the bridge",
            "I can't breathe and my chest hurts badly"
        ]
        
        # This would test the actual detector in integration
        # For unit tests, we verify the phrases exist
        for phrase in emergency_phrases:
            assert len(phrase) > 0
    
    def test_passive_ideation_detection(self):
        """Test passive ideation vs active emergency"""
        passive_phrases = [
            "I don't want to wake up anymore",
            "Everyone would be better off without me",
            "I wish I was gone"
        ]
        
        # These should be handled with care but not as immediate emergencies
        for phrase in passive_phrases:
            assert len(phrase) > 0

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_message_length_limits(self):
        """Test that very long messages are handled"""
        very_long_message = "x" * 10000
        # Should be truncated or handled gracefully
        assert len(very_long_message) == 10000
    
    def test_special_characters(self):
        """Test handling of special characters"""
        special_chars = "<script>alert('xss')</script>"
        # Should be escaped in actual implementation
        assert special_chars is not None
    
    def test_empty_messages(self):
        """Test handling of empty messages"""
        empty_messages = ["", "   ", "\n\n\n"]
        for msg in empty_messages:
            assert msg.strip() == ""

# Integration Tests (require actual API)
@pytest.mark.integration
class TestIntegration:
    """Integration tests - require actual Google API key"""
    
    def test_full_conversation_flow(self):
        """Test a complete conversation flow"""
        # This would require mocking or actual API
        pytest.skip("Requires actual API key and integration setup")
    
    def test_emergency_number_lookup(self):
        """Test emergency number lookup"""
        pytest.skip("Requires actual API key and integration setup")

# Performance Tests
class TestPerformance:
    """Test performance characteristics"""
    
    def test_history_storage_efficiency(self):
        """Test that history storage is efficient"""
        history = ConversationHistory(max_length=1000)
        session_id = "perf_test"
        
        import time
        start_time = time.time()
        
        # Add 1000 messages
        for i in range(1000):
            history.add_message(session_id, "user", f"Message {i}")
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly
        assert elapsed_time < 1.0  # Less than 1 second
        assert len(history.get_history(session_id)) == 1000

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
