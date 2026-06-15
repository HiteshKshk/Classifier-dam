import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Try to load local environment variables from a .env file if it exists.
load_dotenv()

# We initialize the Gemini Client. Under the hood, this will read the GEMINI_API_KEY
# environment variable or look inside our newly loaded .env file.
# If no key is configured, we default to a placeholder string to prevent the client
# initialization from crashing the script at import-time. Subsequent API calls will
# fail gracefully and trigger our fallback engine.
api_key = os.getenv("GEMINI_API_KEY") or "PLACEHOLDER_KEY"
client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are a conservative trust signal classifier for DAM (Defence Against Misinformation).

Your job is to analyze a claim or message and return a structured JSON risk analysis.

STRICT RULES:
1. Never return confidence_ceiling as "high" unless the claim is clearly verifiable from official sources
2. For ambiguous claims, ALWAYS return confidence_ceiling as "low"
3. risk_level and confidence_ceiling are SEPARATE — a claim can be high risk but low confidence
4. Return ONLY valid JSON. No explanation, no prose, no markdown backticks
5. Do not collapse all risky inputs into one generic label — use specific risk_type values
6. recommended_action must be a normal lowercase English sentence/phrase with spaces. DO NOT use snake_case or underscores (e.g. use "do not click on link" instead of "do_not_click_on_link").
7. All risk_signals must be lowercase snake_case strings (e.g. "urgent_deadline", "payment_request", "authority_threat").

ALLOWED VALUES:
- category: "scam", "misinformation", "ambiguous", "safe"
- risk_type: "kyc_scam", "authority_impersonation", "fake_reward", "investment_scam", 
             "health_misinformation", "political_rumor", "tech_misinformation", 
             "social_viral", "safe_factual", "ambiguous_claim"
- risk_level: "high", "medium", "low"
- confidence_ceiling: "high", "medium", "low"

OUTPUT SCHEMA (return exactly this structure):
{
  "input": "<original text>",
  "category": "...",
  "risk_type": "...",
  "risk_level": "...",
  "confidence_ceiling": "...",
  "risk_signals": ["...", "..."],
  "evidence_needed": ["...", "..."],
  "recommended_action": "...",
  "uncertainty_note": "..."
}
"""

def normalize_text(text: str) -> str:
    """
    Even with clear instructions, LLMs can sometimes slip and return actions 
    in snake_case (e.g. "do_not_click"). This cleans it up to standard lowercase with spaces.
    """
    if not text:
        return text
    text = text.replace("_", " ").lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def normalize_signal(signal: str) -> str:
    """
    Ensures that custom risk signals are uniformly formatted as snake_case 
    to pass validation and stay clean in our final datasets.
    """
    if not signal:
        return signal
    signal = signal.lower().strip()
    signal = signal.replace("-", "_").replace(" ", "_")
    signal = re.sub(r'[^a-z0-9_]', '', signal)
    signal = re.sub(r'_+', '_', signal)
    return signal

def classify(text: str, pre_signals: list) -> dict:
    """
    Queries Gemini to analyze the input text and pre-screened signals, returning
    the final structured classification data.
    """
    user_message = f"""
Pre-screening signals detected by rule layer: {pre_signals}

Claim to classify:
\"{text}\"

Return the JSON analysis now. No markdown, no backticks, just raw JSON.
"""

    full_prompt = SYSTEM_PROMPT + "\n\n" + user_message

    # Crucial step: We disable standard safety blocks (setting them to BLOCK_NONE)
    # since we are deliberately feeding scam, harassment, and fraud messages 
    # to the classifier for testing. Otherwise, the API blocks the request.
    config = types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt,
        config=config
    )

    raw = response.text.strip()

    # Sometimes models include markdown fences (```json ... ```) despite strict prompts.
    # We strip these out to prevent JSON parsing issues.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    # Apply our cleanup/normalization routines to guarantee output consistency
    if isinstance(data, dict):
        if "recommended_action" in data and isinstance(data["recommended_action"], str):
            data["recommended_action"] = normalize_text(data["recommended_action"])
        
        if "risk_signals" in data and isinstance(data["risk_signals"], list):
            data["risk_signals"] = [normalize_signal(s) for s in data["risk_signals"] if isinstance(s, str)]
            
    return data