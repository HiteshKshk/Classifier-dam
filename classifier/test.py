# from rules import extract_signals, get_risk_level_from_signals
# from llm_classifier import classify
# from validator import validate
# import json

# # Type any claim here to test
# test_claim = "Your Aadhaar card will be cancelled in 24 hours. Call 9XXXXXX immediately."

# print("Testing claim:", test_claim)
# print("-" * 50)

# # Rule layer
# signals = extract_signals(test_claim)
# risk = get_risk_level_from_signals(signals)
# print("Rule signals found:", signals)
# print("Rule risk level:", risk)

# # LLM layer
# output = classify(test_claim, signals)
# print("\nFull JSON output:")
# print(json.dumps(output, indent=2))

# # Validate
# is_valid, error = validate(output)
# print("\nValidation:", "PASS" if is_valid else f"FAIL - {error}")