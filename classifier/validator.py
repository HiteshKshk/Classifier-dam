import jsonschema

SCHEMA = {
    "type": "object",
    "required": ["input", "category", "risk_type", "risk_level", 
                 "confidence_ceiling", "risk_signals", "evidence_needed",
                 "recommended_action", "uncertainty_note"],
    "properties": {
        "category": {"enum": ["scam", "misinformation", "ambiguous", "safe"]},
        "risk_type": {"enum": [
            "kyc_scam", "authority_impersonation", "fake_reward",
            "investment_scam", "health_misinformation", "political_rumor",
            "tech_misinformation", "social_viral", "safe_factual", "ambiguous_claim"
        ]},
        "risk_level": {"enum": ["high", "medium", "low"]},
        "confidence_ceiling": {"enum": ["high", "medium", "low"]},
        "risk_signals": {"type": "array"},
        "evidence_needed": {"type": "array"},
    }
}

def validate(output: dict) -> tuple[bool, str]:
    try:
        jsonschema.validate(instance=output, schema=SCHEMA)
        return True, "valid"
    except jsonschema.ValidationError as e:
        return False, str(e.message)