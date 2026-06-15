import re

# These patterns represent classic indicators of spam, scams, and misinformation.
# We use regular expression word boundaries (\b) here to prevent silly false positives.
# For example, we don't want "apply" matching "pay", or words ending in "rs" like 
# "cylinders" or "hours" triggering "rs " (Rupees) payment requests.
SIGNAL_PATTERNS = {
    # Scammers love to create artificial urgency to panic the victim
    "urgent_deadline": [
        r"\b24\s*hours\b", r"\bexpires?\b", r"\bimmediately\b", r"\btonight\b", r"\b2\s*hours\b",
        r"\bmidnight\b", r"\bbefore\b", r"\blast\s*chance\b", r"\burgent\b", r"\bdeactivate\b"
    ],
    # Demanding money, deposits, or digital assets
    "payment_request": [
        r"\bpay\b", r"\bprocessing\s+fee\b", r"\bdeposits?\b", r"\bsend\b", r"\btransfers?\b",
        r"\bwallets?\b", r"\brs\.?\s*\d+", r"\busdt\b", r"\bminimum\b"
    ],
    # Impersonating police, government bodies (e.g., TRAI, Aadhaar) to threaten legal action
    "authority_threat": [
        r"\bcybercrime\b", r"\bpolice\b", r"\barrests?\b", r"\bcourt\b", r"\baadhaar\b",
        r"\btrai\b", r"\bcase\s+registered\b", r"\billegal\s+activity\b", r"\bofficer\b"
    ],
    # Links pointing to lookalike verify pages, bit.ly links, or suspicious TLDs like .info
    "suspicious_link": [
        r"\bbit\.ly\b", r"\btinyurl\b", r"\bclick\s+here\b", r"\.info\b", r"\bsecure-verify\b",
        r"https?://", r"\bverify\.in\b", r"\bupdate-now\b"
    ],
    # Winning a lottery or prize you never entered
    "fake_reward": [
        r"\byou\s+have\s+won\b", r"\bcongratulations\b", r"\blucky\s+draw\b", r"\bselected\b",
        r"\bprizes?\b", r"\blakh\b", r"\bgifts?\b"
    ],
    # Demanding you forward the hoax to keep your account active or spread panic
    "forward_pressure": [
        r"\bforward\s+this\b", r"\bshare\s+with\b", r"\bsend\s+to\b", r"\bforward\s+to\b",
        r"\bshare\s+before\b", r"\bgets\s+deleted\b"
    ],
    # "Get rich quick" investment scams
    "guaranteed_return": [
        r"\bguaranteed\b", r"\bguaranteed\s+return\b", r"\bfixed\s+return\b",
        r"\bno\s+risk\b", r"100%"
    ],
    # Dangerous claims about unscientific medical cures
    "health_miracle": [
        r"\bcures?\s+permanently\b", r"doctors\s+don't\s+want", r"\bmiracle\b",
        r"\bremedy\b", r"\b7\s*days\b", r"\bprevents?\s+cancer\b"
    ]
}

def extract_signals(text: str) -> list:
    """
    Scans the text against our pre-defined threat patterns.
    Returns a list of matching category names.
    """
    text_lower = text.lower()
    found = []
    for signal_name, patterns in SIGNAL_PATTERNS.items():
        for pattern in patterns:
            # Using re.search to support word boundary and digit checks
            if re.search(pattern, text_lower):
                found.append(signal_name)
                break  # Finding one keyword per category is enough to raise the flag
    return found

def get_risk_level_from_signals(signals: list) -> str:
    """
    Estimates the threat level based on the count and severity of extracted signals.
    """
    # These signals indicate direct, immediate threats of financial loss or arrest
    high_signals = {"payment_request", "authority_threat", 
                    "suspicious_link", "guaranteed_return"}
    
    # If there are a lot of suspicious flags, it's almost certainly high risk
    if len(signals) >= 3:
        return "high"
    # Having even one critical threat signal gets pushed to high risk immediately
    elif len(signals) >= 1 and any(s in high_signals for s in signals):
        return "high"
    # Minor warning flags represent medium risk
    elif len(signals) >= 1:
        return "medium"
    # No matches found: low risk
    else:
        return "low"