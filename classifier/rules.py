SIGNAL_PATTERNS = {
    "urgent_deadline": [
        "24 hours", "expires", "immediately", "tonight", "2 hours",
        "midnight", "before", "last chance", "urgent", "deactivate"
    ],
    "payment_request": [
        "pay", "processing fee", "deposit", "send", "transfer",
        "wallet", "rs ", "usdt", "minimum"
    ],
    "authority_threat": [
        "cybercrime", "police", "arrest", "court", "aadhaar",
        "trai", "case registered", "illegal activity", "officer"
    ],
    "suspicious_link": [
        "bit.ly", "tinyurl", "click here", ".info", "secure-verify",
        "http://", "verify.in", "update-now"
    ],
    "fake_reward": [
        "you have won", "congratulations", "lucky draw", "selected",
        "prize", "lakh", "gift"
    ],
    "forward_pressure": [
        "forward this", "share with", "send to", "forward to",
        "share before", "gets deleted"
    ],
    "guaranteed_return": [
        "guaranteed", "guaranteed return", "fixed return",
        "no risk", "100%"
    ],
    "health_miracle": [
        "cures permanently", "doctors don't want", "miracle",
        "remedy", "7 days", "prevents cancer"
    ]
}

def extract_signals(text: str) -> list:
    text_lower = text.lower()
    found = []
    for signal_name, keywords in SIGNAL_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                found.append(signal_name)
                break  # one match per signal type is enough
    return found

def get_risk_level_from_signals(signals: list) -> str:
    high_signals = {"payment_request", "authority_threat", 
                    "suspicious_link", "guaranteed_return"}
    if len(signals) >= 3:
        return "high"
    elif len(signals) >= 1 and any(s in high_signals for s in signals):
        return "high"
    elif len(signals) >= 1:
        return "medium"
    else:
        return "low"