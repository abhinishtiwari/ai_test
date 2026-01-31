# Soulene - Mental Health Support Chatbot

A compassionate AI-powered mental health support system with advanced safety mechanisms.

## 🌟 Features

- **Multi-Layer Safety System**: Pre-check counter, emergency detection, and post-response refinement
- **Loop Detection**: Prevents repetitive responses and stuck conversations
- **Emergency Support**: Automatic detection and provision of emergency resources
- **Context-Aware**: Maintains conversation history for better understanding
- **Location-Based Emergency Numbers**: Attempts to provide relevant local emergency contacts

## 🏗️ Architecture

```
User Message
   ↓
Pre-Check Counter (Safety Analysis)
   ↓
Emergency Detector (Crisis Detection)
   ↓
Soulene AI (Empathetic Draft Response)
   ↓
Counter-AI (Safety Refinement)
   ↓
Loop & Repetition Control
   ↓
Final Reply
```

### Components

1. **Pre-Check Counter**: Analyzes incoming messages for immediate safety risks before generating response
2. **Emergency Detector**: Identifies crisis situations requiring immediate intervention
3. **Soulene AI**: Generates empathetic, human-like responses
4. **Counter-AI**: Refines responses for safety, quality, and ethical concerns
5. **Loop Controller**: Prevents repetitive grounding techniques and stuck patterns
6. **Conversation History Manager**: Tracks context and patterns across the conversation

## 📋 Prerequisites

- Python 3.9 or higher
- Google Generative AI API key
- Modern web browser

## 🚀 Installation

### 1. Clone or Download

```bash
# Create project directory
mkdir soulene-server
cd soulene-server
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install google-generativeai langchain langchain-google-genai flask flask-cors python-dotenv
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
DEBUG_MODE=False
```

**Important**: Never commit your `.env` file to version control!

### 4. Secure Your API Key

**CRITICAL**: The current code has a hardcoded API key as fallback. Before deploying:

1. Remove the hardcoded key from `Config.API_KEY`
2. Change this line in `soulene_server.py`:
   ```python
   API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDCnHKDc49Qfxh1expBsB-S_CIUvCBBQ3Y')
   ```
   To:
   ```python
   API_KEY = os.getenv('GOOGLE_API_KEY')
   if not API_KEY:
       raise ValueError("GOOGLE_API_KEY environment variable not set")
   ```

## 🎯 Usage

### Starting the Server

```bash
python soulene_server.py
```

You should see:

```
======================================================================
🌟 SOULENE SERVER
======================================================================
Server running at: http://localhost:5000
Health check: http://localhost:5000/health
Chat endpoint: http://localhost:5000/chat
======================================================================
Architecture Pipeline:
  User Message → Pre-Check Counter → Emergency Detector
  → Soulene Draft → Counter-AI → Loop Control → Final Reply
======================================================================
```

### Opening the Chat Interface

1. Open `chat_interface.html` in your web browser
2. Start chatting!

### Using the API Directly

#### Health Check

```bash
curl http://localhost:5000/health
```

#### Send a Message

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I'm feeling overwhelmed today",
    "session_id": "test_session_123"
  }'
```

#### Clear Session

```bash
curl -X POST http://localhost:5000/chat/clear \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123"
  }'
```

## 📡 API Reference

### POST /chat

Send a message and receive a response.

**Request Body:**
```json
{
  "message": "Your message here",
  "history": [],  // Optional: previous conversation
  "session_id": "unique_session_id"  // Optional: defaults to 'default'
}
```

**Response:**
```json
{
  "reply": "Soulene's response",
  "is_emergency": false,
  "emergency_type": "none",
  "pre_check_data": {
    "risk_level": "none",
    "risk_type": "none",
    "requires_intervention": false
  },
  "loop_detected": false
}
```

### POST /chat/clear

Clear a session's conversation history.

**Request Body:**
```json
{
  "session_id": "session_to_clear"
}
```

**Response:**
```json
{
  "status": "cleared",
  "session_id": "session_to_clear"
}
```

### GET /health

Check server health status.

**Response:**
```json
{
  "status": "ok",
  "message": "Soulene server is running",
  "timestamp": "2025-01-31T10:30:00.000Z"
}
```

## 🔒 Security Considerations

### Current Issues

1. **Exposed API Key**: Remove hardcoded key before production
2. **No Rate Limiting**: Add rate limiting to prevent abuse
3. **No Authentication**: Consider adding user authentication
4. **CORS Wide Open**: Restrict CORS to specific origins in production
5. **No Input Validation**: Add robust input sanitization
6. **In-Memory Storage**: Consider using Redis or database for sessions

### Recommended Improvements

```python
# Add rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# Restrict CORS
CORS(app, resources={
    r"/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"]
    }
})

# Add input validation
from werkzeug.utils import escape

def sanitize_input(text):
    return escape(text)[:1000]  # Limit length
```

## 🧪 Testing

Run basic tests:

```bash
# Test server health
curl http://localhost:5000/health

# Test chat endpoint
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Test emergency detection
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to end it all"}'
```

## 📊 Monitoring and Logging

The server logs to console with INFO level by default. To change logging:

```python
# In .env
LOG_LEVEL=DEBUG
LOG_FILE=soulene.log
```

View logs in real-time:

```bash
tail -f soulene.log
```

## 🔧 Troubleshooting

### Server won't start

1. Check Python version: `python --version` (should be 3.9+)
2. Verify dependencies: `pip install -r requirements.txt`
3. Check API key is set: `echo $GOOGLE_API_KEY`

### Chat interface shows "Offline"

1. Verify server is running: `curl http://localhost:5000/health`
2. Check browser console for errors (F12)
3. Ensure CORS is configured correctly

### Responses are slow

1. Check your internet connection
2. Verify Google API quota limits
3. Consider implementing response caching

### Emergency detection not working

1. Check logs for errors in emergency detector
2. Verify model has proper instructions
3. Test with explicit emergency phrases

## 🚀 Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 soulene_server:app
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GOOGLE_API_KEY=""
ENV FLASK_PORT=5000

EXPOSE 5000

CMD ["python", "soulene_server.py"]
```

Build and run:

```bash
docker build -t soulene-server .
docker run -p 5000:5000 -e GOOGLE_API_KEY=your_key soulene-server
```

### Environment Variables for Production

```env
GOOGLE_API_KEY=your_production_key
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
DEBUG_MODE=False
LOG_LEVEL=WARNING
MAX_HISTORY_LENGTH=100
```

## 📝 Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | Required | Google Generative AI API key |
| `FLASK_PORT` | 5000 | Server port |
| `FLASK_HOST` | 0.0.0.0 | Server host |
| `DEBUG_MODE` | True | Enable Flask debug mode |
| `MAX_HISTORY_LENGTH` | 50 | Maximum conversation history |
| `CONTEXT_WINDOW_SIZE` | 10 | Recent context window |

## 🤝 Contributing

This is a mental health support tool. Contributions should prioritize:

1. **Safety First**: Any changes must maintain or improve safety mechanisms
2. **User Privacy**: Never log or store sensitive user information
3. **Ethical AI**: Responses must be compassionate and non-judgmental
4. **Code Quality**: Follow existing patterns and document changes

## ⚠️ Disclaimer

**THIS IS NOT A REPLACEMENT FOR PROFESSIONAL MENTAL HEALTH CARE**

Soulene is designed to provide emotional support and encouragement, but:

- It is NOT a licensed therapist or counselor
- It should NOT be used for medical diagnosis or treatment
- In case of emergency, always contact local emergency services
- If experiencing suicidal thoughts, contact a crisis hotline immediately

## 📞 Emergency Resources

### International
- **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/

### United States
- **988 Suicide & Crisis Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741

### United Kingdom
- **Samaritans**: 116 123

### India
- **AASRA**: +91 9820466726
- **Vandrevala Foundation**: 1860 2662 345

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- Google Generative AI for the underlying models
- LangChain for the AI orchestration framework
- Flask for the web framework

## 📧 Support

For issues, questions, or concerns:
- Open an issue on GitHub
- Contact: [Your contact information]

---

**Remember**: If you or someone you know is in immediate danger, please contact emergency services or a crisis hotline immediately.
