from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a conservative trust signal classifier for DAM (Defence Against Misinformation).

Your job is to analyze a claim or message and return a structured JSON risk analysis.

STRICT RULES:
1. Never return confidence_ceiling as "high" unless the claim is clearly verifiable from official sources
2. For ambiguous claims, ALWAYS return confidence_ceiling as "low"
3. risk_level and confidence_ceiling are SEPARATE — a claim can be high risk but low confidence
4. Return ONLY valid JSON. No explanation, no prose, no markdown backticks
5. Do not collapse all risky inputs into one generic label — use specific risk_type values

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

def classify(text: str, pre_signals: list) -> dict:
    user_message = f"""
Pre-screening signals detected by rule layer: {pre_signals}

Claim to classify:
\"{text}\"

Return the JSON analysis now. No markdown, no backticks, just raw JSON.
"""

    full_prompt = SYSTEM_PROMPT + "\n\n" + user_message

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)