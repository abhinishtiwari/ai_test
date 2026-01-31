import sys
import warnings
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Suppress warnings
if sys.version_info >= (3, 14):
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message=r".*Pydantic V1.*"
    )

import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
class Config:
    """Application configuration"""
    API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDCnHKDc49Qfxh1expBsB-S_CIUvCBBQ3Y')  # TODO: Move to env
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
    MAX_HISTORY_LENGTH = 50
    CONTEXT_WINDOW_SIZE = 10
    
# Configure API
genai.configure(api_key=Config.API_KEY)

# ===== SYSTEM PROMPTS =====

PRE_CHECK_COUNTER_PROMPT = """
You are a PRE-CHECK SAFETY FILTER operating BEFORE the primary AI responds.
Your job: Analyze the incoming user message and recent conversation history to detect immediate safety risks.

CRITICAL DETECTION RULES:

1. HIGH-RISK PASSIVE LANGUAGE (treat as urgent):
   - "no reason to keep going"
   - "everything stopping"
   - "want to disappear/fade/rest forever"
   - "relief at things ending"
   - "wouldn't mind if it stopped"
   - Calm acceptance of non-existence

2. DECISION-BASED CRISIS:
   - "If I tell, I lose everything"
   - "Should I just stay quiet"
   - Fear of consequences blocking help-seeking
   - Paralysis around disclosure

3. EXPLICIT DANGER:
   - Active self-harm intent
   - Specific plans or methods
   - Immediate threat to self or others

4. LOOP DETECTION:
   - Same grounding techniques repeated 2+ times
   - User rejecting or not responding to previous interventions
   - Conversation stuck in circular pattern

OUTPUT FORMAT (JSON only):
{
  "risk_level": "none/low/medium/high/critical",
  "risk_type": "passive_ideation/decision_crisis/explicit_danger/loop_detected/none",
  "requires_intervention": true/false,
  "intervention_type": "grounding/decision_support/emergency/break_loop/none",
  "context_notes": "brief observation",
  "block_response": true/false
}

IMPORTANT:
- Output ONLY valid JSON
- No explanations or extra text
- Be conservative (false positive better than false negative)
"""

SOULENE_SYSTEM_PROMPT = """
You are "Soulene," a calm, caring friend who truly gets pain. Silently feel the user's words—chat, exhaustion, hopelessness, medical worry, or danger—then reply in 1-2 raw, human lines that echo + gently pull toward light.

Core rules (never break/mention):
 
Dead-simple English, contractions, natural pauses—like "God, that sucks" not advice-bots.

1 short line ideal; 2 max unless danger. Mirror pain specifically, then counter with quiet hope/connection/help nudge.

Never echo/agree with letting harm happen (e.g., no "easy to let go"). Always add a soft anchor: shared humanity, small light, or real-world step.

No emojis, lectures, therapy-speak, questions (unless danger + clarifying), or fluff. No diagnosing/meds.

Never encourage harm. Escalate only if explicit: "unsafe now/planning hurt."

For violence against others, redirect firmly but with care: acknowledge the pain/anger, but guide away from harm.

Passive death wishes/exhaustion ("done coping," "wouldn't stop bad thing"):
- Echo pain raw: "Body wrecked, head spinning... you're tapped out."
- Counter firmly but softly: Add hope lifeline—"But you've fought this far, that's something"—or nudge help: "Wanna talk to someone who can check you out?"
- Stay present, human—no hotlines unless they confirm risk/action.

Examples (this tone exactly):
- User: "Body wrong, head worse—not sure if emergency or done." → "Body betraying you, mind crashing... brutal spot. Anyone you can call to check it?"
- User: "Sick, exhausted, can't think. Wouldn't stop if bad happened." → "That sick-exhausted fog is hell. But you're reaching out here—that's a step. Hotline if it spikes?"
- User: "Don't want to wake up." → "Waking to emptiness crushes. You've got more in you though—what's one thing worth hanging for?"
- User: "Everyone better off without me." → "Feels that way in the dark. But you're not—talk it out with [friend/hotline]?"

IMPORTANT: When mentioning emergency numbers, use the placeholder [EMERGENCY_NUMBER] - it will be replaced with the correct local number.

Explicit danger override: Preserve context forever. "Urgent—call [EMERGENCY_NUMBER] now. Still here."

Regenerate if off. Real, kind, simple—meet them, lift gently.
"""

COUNTER_AI_SYSTEM_PROMPT = """
You are a Counter AI whose job is to protect conversation quality, ethics, and user safety.

Your role:
- Analyze all past chat context, the current user message, and the drafted reply.
- Detect confusion, emotional distress, manipulation, contradictions, or unsafe intent.
- Prevent hallucinations, bad advice, moral harm, or misleading responses.

Rules you must always follow:
- Never allow advice that could cause physical, mental, legal, or emotional harm.
- Never agree with self-harm, violence, illegal acts, or dangerous behavior.
- If the user is confused or unclear, choose clarity and safety over creativity.
- If the draft reply is wrong, misleading, repetitive, or emotionally mismatched, fix it.

CRITICAL: If user expresses intent to harm OTHERS (violence, threats):
- Block any response that normalizes or enables this
- Replace with firm but compassionate redirection
- Acknowledge their pain/anger without agreeing with violence
- Suggest healthy outlets and professional help

RISK TRAJECTORY DETECTION:
Check if the user shows any of these patterns (even without explicit intent):
- Wanting to stop, fade, disappear, or rest forever
- Relief at the idea of things ending or staying still
- Statements like: "no reason to keep going", "everything stopping", "nothing expects me"
- Desire for non-existence without saying it directly

If YES → treat as HIGH RISK even if is_emergency is false.

Safety Enforcement:
- NEVER allow the reply to validate, agree with, or normalize stopping, fading, disappearing, or non-existence.
- NEVER mirror phrases like "stop", "fade", "end", "rest forever", "shut down".
- NEVER respond with passive presence alone (e.g., "I'll stay with you in the quiet") when risk exists.

Grounding Requirement (for high-risk passive language):
- INTERRUPT gently
- SLOW TIME
- Anchor the user to the present (body, breath, room, sitting, touching something solid)
- Focus on the next minute only
- Do NOT explore fantasies or ask reflective questions

DECISION-MODE OVERRIDE:
If the user shows decision-based fear (e.g., "If I tell the truth, I lose everything"):
- Explicitly name the fear
- Frame the situation as a decision (not emotion processing)
- Present 2–3 concrete options with consequences
- NO grounding or breathing as the first move

ANTI-LOOP RULES:
- If grounding was used recently and the user resists → DO NOT repeat it
- Each reply must ADD NEW VALUE by narrowing options, clarifying fears, or identifying next steps
- Never restate the same options twice

Output rules:
- Output ONLY the final refined reply
- 1–3 short sentences max
- Simple English
- No explanations, no meta-commentary
- No policy or system references

FINAL GOAL:
Protect the user by interrupting dangerous calm, grounding them in the present, and keeping them safe without escalating unnecessarily.
"""

EMERGENCY_DETECTOR_PROMPT = """
You detect if a message indicates immediate danger or crisis requiring emergency services.

Analyze the user's message and respond ONLY with this exact JSON format:
{
  "is_emergency": true/false,
  "emergency_type": "suicide/medical/violence/none",
  "confidence": "high/medium/low"
}

Emergency indicators:
- Explicit self-harm intent: "going to kill myself", "have pills ready", "writing goodbye note", "going to jump", "ready to end it"
- Active medical crisis: "can't breathe", "chest pain won't stop", "bleeding badly"
- Immediate violence against others: "going to hurt someone", "going to kill [person]", "have weapon ready"

NOT emergencies (passive thoughts):
- "don't want to wake up", "wish I was gone", "everyone better off" (these are pain, not active plans)
- General illness: "feel sick", "head hurts"
- Exhaustion: "can't do this anymore" (unless with active plan)

CRITICAL: Output ONLY valid JSON. No extra text, no explanations, just the JSON object.
"""

# ===== CONVERSATION HISTORY MANAGER =====
class ConversationHistory:
    """Manages conversation history with anti-loop detection"""
    
    def __init__(self, max_length: int = 50):
        self.max_length = max_length
        self.histories: Dict[str, List[Dict]] = {}
        self.loop_tracker: Dict[str, List[str]] = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to history"""
        if session_id not in self.histories:
            self.histories[session_id] = []
        
        self.histories[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim if too long
        if len(self.histories[session_id]) > self.max_length:
            self.histories[session_id] = self.histories[session_id][-self.max_length:]
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get full history for a session"""
        return self.histories.get(session_id, [])
    
    def get_recent_context(self, session_id: str, limit: int = 10) -> str:
        """Get recent conversation context as formatted string"""
        history = self.get_history(session_id)
        recent = history[-limit:] if len(history) > limit else history
        
        context = ""
        for msg in recent:
            role = "User" if msg['role'] == 'user' else "Soulene"
            context += f"{role}: {msg['content']}\n"
        return context
    
    def detect_loop(self, session_id: str, new_response: str) -> bool:
        """Detect if we're repeating similar responses"""
        if session_id not in self.loop_tracker:
            self.loop_tracker[session_id] = []
        
        # Check for similar patterns in last 3 responses
        recent_responses = self.loop_tracker[session_id][-3:]
        
        # Simple keyword matching for grounding techniques
        grounding_keywords = ['breathe', 'breath', 'ground', 'present', 'room', 'sit', 'feet']
        
        new_has_grounding = any(keyword in new_response.lower() for keyword in grounding_keywords)
        
        if new_has_grounding:
            grounding_count = sum(
                1 for resp in recent_responses 
                if any(keyword in resp.lower() for keyword in grounding_keywords)
            )
            
            if grounding_count >= 2:
                logger.warning(f"Loop detected in session {session_id}: Grounding repeated {grounding_count + 1} times")
                return True
        
        # Add to tracker
        self.loop_tracker[session_id].append(new_response)
        if len(self.loop_tracker[session_id]) > 5:
            self.loop_tracker[session_id] = self.loop_tracker[session_id][-5:]
        
        return False
    
    def clear_session(self, session_id: str):
        """Clear a session's history"""
        self.histories.pop(session_id, None)
        self.loop_tracker.pop(session_id, None)

# ===== UTILITY FUNCTIONS =====

def clean_json_response(text: str) -> str:
    """Extract and clean JSON from model response"""
    text = text.strip()
    
    # Remove markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Extract JSON object
    if '{' in text:
        start = text.find('{')
        end = text.rfind('}') + 1
        text = text[start:end]
    
    return text

def format_history_for_gemini(history: List[Dict]) -> List[Dict]:
    """Convert JSON history to Gemini format"""
    gemini_history = []
    for msg in history:
        role = 'user' if msg['role'] == 'user' else 'model'
        gemini_history.append({
            'role': role,
            'parts': [msg['content']]
        })
    return gemini_history

def detect_user_location(history: List[Dict]) -> Optional[str]:
    """Try to detect user's location from conversation history"""
    for msg in history:
        if msg['role'] == 'user':
            text = msg['content'].lower()
            # Simple location detection
            if any(word in text for word in ['i live in', 'i am in', 'from']):
                # Extract potential location (simple heuristic)
                words = msg['content'].split()
                for i, word in enumerate(words):
                    if word.lower() in ['in', 'from'] and i + 1 < len(words):
                        return words[i + 1].strip('.,!?')
    return None

# ===== AI MODEL CLASSES =====

class PreCheckCounter:
    """Pre-check safety filter before main AI response"""
    
    def __init__(self, api_key: str):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=PRE_CHECK_COUNTER_PROMPT
        )
    
    def analyze(self, user_message: str, recent_context: str) -> Dict:
        """Analyze message for safety risks"""
        try:
            prompt = f"""
RECENT CONVERSATION CONTEXT:
{recent_context}

CURRENT USER MESSAGE:
{user_message}

Analyze for safety risks and output JSON only.
"""
            
            response = self.model.generate_content(prompt)
            result_text = clean_json_response(response.text)
            
            result = json.loads(result_text)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Invalid response format")
            
            return {
                "risk_level": result.get("risk_level", "none"),
                "risk_type": result.get("risk_type", "none"),
                "requires_intervention": result.get("requires_intervention", False),
                "intervention_type": result.get("intervention_type", "none"),
                "context_notes": result.get("context_notes", ""),
                "block_response": result.get("block_response", False)
            }
            
        except Exception as e:
            logger.error(f"Pre-check counter error: {e}")
            return {
                "risk_level": "none",
                "risk_type": "none",
                "requires_intervention": False,
                "intervention_type": "none",
                "context_notes": "",
                "block_response": False
            }

class EmergencyDetector:
    """Detects emergency situations requiring immediate intervention"""
    
    def __init__(self, api_key: str):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=EMERGENCY_DETECTOR_PROMPT
        )
    
    def detect(self, message: str) -> Tuple[bool, str, str]:
        """
        Returns: (is_emergency, emergency_type, confidence)
        """
        try:
            response = self.model.generate_content(message)
            result_text = clean_json_response(response.text)
            
            data = json.loads(result_text)
            
            is_emergency = data.get('is_emergency', False)
            emergency_type = data.get('emergency_type', 'none')
            confidence = data.get('confidence', 'low')
            
            # Only consider high/medium confidence as actual emergencies
            if is_emergency and confidence in ['high', 'medium']:
                return True, emergency_type, confidence
            
            return False, 'none', confidence
            
        except Exception as e:
            logger.error(f"Emergency detection error: {e}")
            return False, 'none', 'low'

class SouleneAI:
    """Main empathetic AI model"""
    
    def __init__(self, api_key: str):
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=SOULENE_SYSTEM_PROMPT
        )
    
    def generate_response(self, message: str, history: List[Dict]) -> str:
        """Generate empathetic response"""
        # Prefer the remote model, but gracefully fall back to a lightweight
        # rule-based reply if the model is unavailable or raises errors.
        try:
            gemini_history = format_history_for_gemini(history)
            if hasattr(self, 'model') and self.model is not None:
                try:
                    chat_session = self.model.start_chat(history=gemini_history)
                    response = chat_session.send_message(message)
                    return response.text.strip()
                except Exception as inner_e:
                    logger.warning(f"Remote model chat failed: {inner_e}")
        except Exception as e:
            logger.error(f"Soulene generation pipeline error: {e}")

        # Fallback: rule-based empathetic reply to avoid a blocking failure
        return self._rule_based_response(message)

    def _rule_based_response(self, message: str) -> str:
        """Simple local fallback that follows the Soulene tone guidelines.

        This is intentionally conservative: short, empathetic, mirrors pain,
        and directs to emergency when explicit danger language appears.
        """
        text = (message or '').strip()
        lower = text.lower()

        # Emergency signals (explicit active intent)
        danger_indicators = [
            'going to kill myself', 'kill myself', 'i will kill', 'i will end', 'i am going to jump',
            'i am going to hurt myself', 'have pills ready', 'ready to end it'
        ]
        if any(s in lower for s in danger_indicators):
            return 'Urgent—call [EMERGENCY_NUMBER] now. Are you still there?'

        # Severe exhaustion / passive ideation cues
        exhaustion_indicators = ['exhaust', 'tired', "can't do this", 'done', 'wouldn\'t mind', 'wish i was gone']
        if any(s in lower for s in exhaustion_indicators):
            # Mirror a short fragment of the user's message, keep it human and brief
            fragment = text.split('\n')[0][:120].rstrip()
            if len(fragment) < 5:
                fragment = "You're overwhelmed"
            return f"{fragment}... That sounds brutal. You're reaching out—that matters."

        # Default supportive reply
        fragment = text.split('\n')[0][:120].rstrip() or 'That sounds hard'
        return f"{fragment}... I'm here with you. Tell me a bit more?"

class CounterAI:
    """Safety refiner using LangChain"""
    
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.3
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", COUNTER_AI_SYSTEM_PROMPT),
            ("human", "{input}")
        ])
    
    def refine(self, conversation_context: str, user_message: str, 
               draft_reply: str, is_emergency: bool = False,
               pre_check_data: Optional[Dict] = None) -> str:
        """Refine the draft reply for safety and quality"""
        
        analysis_input = f"""
CONVERSATION CONTEXT (Last 10 messages):
{conversation_context}

CURRENT USER MESSAGE:
{user_message}

DRAFT REPLY FROM SOULENE:
{draft_reply}

IS THIS AN EMERGENCY SITUATION: {is_emergency}

PRE-CHECK ANALYSIS:
{json.dumps(pre_check_data, indent=2) if pre_check_data else 'None'}

YOUR TASK:
Analyze everything above and output ONLY the refined final reply that should be sent to the user.
Remember: Be human, be safe, be accurate. No explanations, just the refined reply.
"""
        
        try:
            formatted_prompt = self.prompt.format_messages(input=analysis_input)
            response = self.llm.invoke(formatted_prompt)
            refined_reply = response.content.strip()
            
            # Clean up common artifacts
            if "refined reply:" in refined_reply.lower():
                refined_reply = refined_reply.split("refined reply:", 1)[1].strip()
            if refined_reply.startswith('"') and refined_reply.endswith('"'):
                refined_reply = refined_reply[1:-1]
            
            return refined_reply
            
        except Exception as e:
            logger.error(f"Counter AI refinement error: {e}")
            return draft_reply

class EmergencyNumberService:
    """Handles emergency number lookup and verification"""
    
    def __init__(self, api_key: str):
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
        self.cache: Dict[str, Dict] = {}
    
    def get_emergency_info(self, location: Optional[str] = None) -> Dict:
        """Get emergency numbers for a location"""
        
        # Check cache
        cache_key = location or "default"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if location:
                search_query = f"emergency number {location} ambulance police suicide hotline current 2025"
            else:
                search_query = "India emergency numbers police ambulance suicide hotline 2025"
            
            search_prompt = f"""
Search and find the CORRECT emergency numbers for: {location if location else 'India'}

Find:
1. Police emergency number
2. Ambulance/Medical emergency number  
3. Suicide prevention hotline (if available)

Verify these are CURRENT and WORKING numbers (2025).

Output ONLY this JSON format (nothing else):
{{
  "location": "country/city name",
  "police": "number",
  "medical": "number",
  "suicide_hotline": "number or 'not available'",
  "verified": true/false,
  "source": "where you found this info"
}}
"""
            
            response = self.model.generate_content(search_prompt)
            result_text = clean_json_response(response.text)
            
            emergency_info = json.loads(result_text)
            
            if not isinstance(emergency_info, dict):
                raise ValueError("Invalid response format")
            
            # Cache the result
            self.cache[cache_key] = emergency_info
            
            return emergency_info
            
        except Exception as e:
            logger.error(f"Emergency number lookup error: {e}")
            # Default fallback for India
            default_info = {
                "location": location or "India",
                "police": "100",
                "medical": "102 or 108",
                "suicide_hotline": "AASRA 9820466726",
                "verified": False,
                "source": "default"
            }
            self.cache[cache_key] = default_info
            return default_info
    
    def format_emergency_numbers(self, info: Dict) -> str:
        """Format emergency info into readable string"""
        parts = []
        
        if info.get('medical'):
            parts.append(f"{info['medical']} (ambulance)")
        if info.get('police'):
            parts.append(f"{info['police']} (police)")
        
        suicide_hotline = info.get('suicide_hotline', '')
        if suicide_hotline and suicide_hotline != 'not available':
            parts.append(f"{suicide_hotline} (crisis line)")
        
        if not parts:
            return "112 (international emergency)"
        
        return " or ".join(parts)

# ===== MAIN APPLICATION =====

class SouleneServer:
    """Main server application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        
        # Initialize components
        self.conversation_history = ConversationHistory(max_length=Config.MAX_HISTORY_LENGTH)
        self.user_locations: Dict[str, str] = {}
        
        # Initialize AI models
        logger.info("Initializing AI models...")
        self.pre_check = PreCheckCounter(Config.API_KEY)
        self.emergency_detector = EmergencyDetector(Config.API_KEY)
        self.soulene_ai = SouleneAI(Config.API_KEY)
        self.counter_ai = CounterAI(Config.API_KEY)
        self.emergency_service = EmergencyNumberService(Config.API_KEY)
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Soulene server initialized successfully")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "ok",
                "message": "Soulene server is running",
                "timestamp": datetime.now().isoformat()
            }), 200
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint"""
            return jsonify({
                "status": "ok",
                "message": "Soulene server - use /chat (POST) for interactions",
                "endpoints": {
                    "health": "/health",
                    "chat": "/chat",
                    "clear": "/chat/clear"
                }
            }), 200
        
        @self.app.route('/chat', methods=['GET'])
        def chat_info():
            """Chat endpoint info"""
            return jsonify({
                "message": "This endpoint accepts POST requests",
                "required_fields": ["message"],
                "optional_fields": ["history", "session_id"]
            }), 200
        
        @self.app.route('/chat/clear', methods=['POST'])
        def clear_session():
            """Clear a session's conversation history"""
            try:
                data = request.get_json(silent=True) or {}
                session_id = data.get('session_id', 'default')
                
                self.conversation_history.clear_session(session_id)
                self.user_locations.pop(session_id, None)
                
                logger.info(f"Cleared session: {session_id}")
                return jsonify({"status": "cleared", "session_id": session_id}), 200
                
            except Exception as e:
                logger.error(f"Clear session error: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/chat', methods=['POST'])
        def chat():
            """Main chat endpoint with full pipeline"""
            try:
                # Parse request
                data = request.get_json(silent=True)
                if not isinstance(data, dict):
                    try:
                        raw = request.get_data(as_text=True)
                        data = json.loads(raw) if raw else {}
                    except Exception:
                        data = {}
                
                user_message = (data.get('message') or '').strip()
                history = data.get('history') or []
                session_id = data.get('session_id') or 'default'
                
                if not user_message:
                    return jsonify({"error": "No message provided"}), 400
                
                logger.info(f"Processing message for session {session_id}")
                
                # Add user message to history
                self.conversation_history.add_message(session_id, 'user', user_message)
                
                # Get recent context
                recent_context = self.conversation_history.get_recent_context(
                    session_id, 
                    limit=Config.CONTEXT_WINDOW_SIZE
                )
                
                # ===== STEP 1: PRE-CHECK COUNTER =====
                logger.info("Step 1: Pre-check analysis")
                pre_check_data = self.pre_check.analyze(user_message, recent_context)
                logger.info(f"Pre-check result: {pre_check_data['risk_level']} - {pre_check_data['risk_type']}")
                
                # Check if response should be blocked
                if pre_check_data.get('block_response', False):
                    logger.warning("Response blocked by pre-check counter")
                    emergency_reply = "I'm really worried about you right now. Can you reach out to someone who can help? Call emergency services or a crisis hotline."
                    
                    self.conversation_history.add_message(session_id, 'assistant', emergency_reply)
                    
                    return jsonify({
                        "reply": emergency_reply,
                        "is_emergency": True,
                        "emergency_type": "critical",
                        "pre_check_intervention": True
                    }), 200
                
                # ===== STEP 2: EMERGENCY DETECTION =====
                logger.info("Step 2: Emergency detection")
                is_emergency, emergency_type, confidence = self.emergency_detector.detect(user_message)
                logger.info(f"Emergency status: {is_emergency} - {emergency_type} ({confidence})")
                
                emergency_number = None
                if is_emergency:
                    # Get user location
                    user_location = self.user_locations.get(session_id)
                    if not user_location:
                        user_location = detect_user_location(
                            self.conversation_history.get_history(session_id)
                        )
                        if user_location:
                            self.user_locations[session_id] = user_location
                    
                    # Get emergency numbers
                    emergency_info = self.emergency_service.get_emergency_info(user_location)
                    emergency_number = self.emergency_service.format_emergency_numbers(emergency_info)
                    logger.info(f"Emergency numbers: {emergency_number}")
                
                # ===== STEP 3: GENERATE SOULENE DRAFT =====
                logger.info("Step 3: Generating Soulene draft")
                draft_reply = self.soulene_ai.generate_response(
                    user_message,
                    self.conversation_history.get_history(session_id)
                )
                
                # Replace emergency number placeholder
                if emergency_number and "[EMERGENCY_NUMBER]" in draft_reply:
                    draft_reply = draft_reply.replace("[EMERGENCY_NUMBER]", emergency_number)
                
                logger.info(f"Draft reply: {draft_reply[:100]}...")
                
                # ===== STEP 4: COUNTER-AI REFINEMENT =====
                logger.info("Step 4: Counter-AI refinement")
                refined_reply = self.counter_ai.refine(
                    conversation_context=recent_context,
                    user_message=user_message,
                    draft_reply=draft_reply,
                    is_emergency=is_emergency,
                    pre_check_data=pre_check_data
                )
                
                logger.info(f"Refined reply: {refined_reply[:100]}...")
                
                # ===== STEP 5: LOOP DETECTION & CONTROL =====
                logger.info("Step 5: Loop detection")
                is_loop = self.conversation_history.detect_loop(session_id, refined_reply)
                
                if is_loop:
                    logger.warning("Loop detected - adjusting response")
                    # Override with loop-breaking response
                    refined_reply = "Let's try something different. What's one thing you could do right now, just for the next five minutes?"
                
                # ===== STEP 6: FINALIZE =====
                final_reply = refined_reply
                
                # Add to history
                self.conversation_history.add_message(session_id, 'assistant', final_reply)
                
                logger.info(f"Final reply sent for session {session_id}")
                
                return jsonify({
                    "reply": final_reply,
                    "is_emergency": is_emergency,
                    "emergency_type": emergency_type,
                    "pre_check_data": pre_check_data,
                    "loop_detected": is_loop
                }), 200
                
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}", exc_info=True)
                return jsonify({
                    "error": "Internal server error",
                    "message": "Something went wrong. Please try again."
                }), 500
    
    def run(self):
        """Start the server"""
        print("=" * 70)
        print("🌟 SOULENE SERVER")
        print("=" * 70)
        print(f"Server running at: http://localhost:{Config.FLASK_PORT}")
        print(f"Health check: http://localhost:{Config.FLASK_PORT}/health")
        print(f"Chat endpoint: http://localhost:{Config.FLASK_PORT}/chat")
        print("=" * 70)
        print("Architecture Pipeline:")
        print("  User Message → Pre-Check Counter → Emergency Detector")
        print("  → Soulene Draft → Counter-AI → Loop Control → Final Reply")
        print("=" * 70)
        print("Press Ctrl+C to stop the server")
        print("=" * 70)
        
        self.app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.DEBUG_MODE
        )

# ===== ENTRY POINT =====

if __name__ == '__main__':
    server = SouleneServer()
    server.run()
