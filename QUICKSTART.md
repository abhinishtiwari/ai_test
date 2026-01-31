# 🚀 Soulene - Quick Start Guide

## Get Running in 3 Steps

### Step 1: Setup Environment

**Create a `.env` file** (rename `env.example.txt` to `.env`):
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
DEBUG_MODE=False
```

**⚠️ SECURITY CRITICAL:**
Before running, you MUST edit `soulene_server.py` line 27 and remove the hardcoded API key:

```python
# CHANGE THIS:
API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDCnHKDc49Qfxh1expBsB-S_CIUvCBBQ3Y')

# TO THIS:
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable must be set")
```

### Step 2: Install Dependencies

**Option A: Using setup script (Linux/Mac)**
```bash
chmod +x setup.sh
./setup.sh
```

**Option B: Manual installation**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Server

**Option A: Using run script**
```bash
chmod +x run_server.sh
./run_server.sh
```

**Option B: Direct Python**
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
```

### Step 4: Open the Chat Interface

Simply open `chat_interface.html` in your web browser!

---

## 🆕 What's New in This Version?

### 1. **Pre-Check Counter** (NEW!)
Analyzes messages BEFORE generating responses to detect:
- Passive suicidal ideation
- Decision-based crises
- Loop patterns
- Risk levels

### 2. **Enhanced Safety**
- 4 layers of protection (was 2)
- Detects "no reason to keep going" type messages
- Breaks out of repetitive grounding loops
- Better emergency number support

### 3. **Better Code Structure**
- Object-oriented design
- Modular components
- Comprehensive error handling
- Production-ready logging

### 4. **Improved UI**
- Server status indicator
- Emergency banners
- Typing indicators
- Auto-save conversations
- Better error messages

---

## 📊 Architecture Flow

```
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Pre-Check Counter  │ ◄── NEW! Analyzes risk before response
│  - Risk assessment  │
│  - Loop detection   │
│  - Crisis detection │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Emergency Detector  │
│  - Active crisis    │
│  - Medical emergency│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Soulene Draft    │
│  - Empathetic AI   │
│  - Human-like tone │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Counter-AI Refine │
│  - Safety check    │
│  - Quality check   │
│  - Ethics check    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Loop Control     │
│  - Pattern detect  │
│  - Break cycles    │
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│  Final Reply    │
└─────────────────┘
```

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "Soulene server is running",
  "timestamp": "2025-01-31T..."
}
```

### Send Test Message
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I feel overwhelmed today"}'
```

### Test Emergency Detection
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to end it all"}'
```

---

## 🔧 Common Issues

### "Server is offline" in UI
1. Check server is running: `curl http://localhost:5000/health`
2. Check console for errors
3. Verify port 5000 is not in use: `lsof -i :5000`

### "GOOGLE_API_KEY not set" error
1. Make sure `.env` file exists
2. Verify it contains `GOOGLE_API_KEY=your_key`
3. Make sure you removed the hardcoded fallback in the code

### Import errors
```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Slow responses
- Check your internet connection
- Verify Google API quota limits
- Monitor logs for API errors

---

## 📁 File Overview

| File | Purpose |
|------|---------|
| `soulene_server.py` | Main server application |
| `chat_interface.html` | Web chat UI |
| `requirements.txt` | Python dependencies |
| `.env` | Configuration (create from env.example.txt) |
| `setup.sh` | Automated setup script |
| `run_server.sh` | Quick start script |
| `test_soulene.py` | Test suite |
| `Dockerfile` | Container image |
| `docker-compose.yml` | Container orchestration |
| `README.md` | Full documentation |
| `DEPLOYMENT.md` | Production deployment guide |
| `IMPROVEMENTS.md` | Change summary |

---

## 🚀 Next Steps

### For Development
1. Run tests: `pytest test_soulene.py -v`
2. Check logs in console
3. Modify prompts in `soulene_server.py` if needed

### For Production
1. Read `DEPLOYMENT.md` thoroughly
2. **Remove hardcoded API key** (critical!)
3. Set `DEBUG_MODE=False` in `.env`
4. Add rate limiting
5. Setup HTTPS/SSL
6. Configure monitoring

### For Docker
```bash
# Build
docker build -t soulene-server .

# Run
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 📞 Emergency Resources

The system will provide location-appropriate emergency numbers, but here are defaults:

**International**: 112
**US**: 988 (Suicide & Crisis Lifeline)
**UK**: 116 123 (Samaritans)
**India**: 9820466726 (AASRA)

---

## ⚠️ Important Reminders

1. **This is NOT a replacement for professional help**
2. **Always prioritize user safety**
3. **Test thoroughly before production use**
4. **Monitor logs and errors**
5. **Keep API keys secure**
6. **Have backup/emergency procedures**

---

## 🎯 Key Features

✅ **Pre-Check Safety Counter** - NEW layer before response
✅ **Loop Detection** - Prevents stuck conversations
✅ **Emergency Support** - Auto-detects crisis situations
✅ **Context-Aware** - Remembers conversation history
✅ **Location-Based Help** - Provides local emergency numbers
✅ **Graceful Degradation** - Works even if components fail
✅ **Production Ready** - Logging, error handling, monitoring
✅ **Easy Deployment** - Docker, scripts, guides

---

## 💡 Tips

- Start with local testing before deploying
- Use the test suite to verify functionality
- Monitor initial conversations closely
- Adjust prompts based on real usage
- Keep documentation updated
- Regular backups if storing data

---

**Need help?** Check the full README.md or DEPLOYMENT.md for detailed information.

**Ready to deploy?** Follow DEPLOYMENT.md for production setup.

**Want to understand changes?** Read IMPROVEMENTS.md for detailed explanations.

---

Built with care for those who need support. 🌟
