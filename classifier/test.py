import sys
import os

# Adjust path so imports work relative to the classifier folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rules import extract_signals, get_risk_level_from_signals
from validator import validate

def test_rule_layer_false_positives():
    print("Running rule layer false positive tests...")
    
    # 1. Verify that 'paytm' does NOT trigger the 'payment_request' rule (which matched substring 'pay' previously)
    text_paytm = "Verify at paytm-secure-verify.info within 6 hours."
    signals_paytm = extract_signals(text_paytm)
    assert "payment_request" not in signals_paytm, f"Failed: paytm matched payment_request. Signals: {signals_paytm}"
    assert "suspicious_link" in signals_paytm, "Failed: suspicious_link not detected"
    print("  [OK] Paytm exclusion test passed.")
    
    # 2. Verify that general words ending in 'rs' followed by a space (like 'cylinders ') do NOT trigger 'payment_request'
    text_cylinders = "The government has announced free LPG cylinders for all BPL families."
    signals_cylinders = extract_signals(text_cylinders)
    assert "payment_request" not in signals_cylinders, f"Failed: 'cylinders ' matched payment_request. Signals: {signals_cylinders}"
    print("  [OK] Plural words ending in 'rs' (cylinders) exclusion test passed.")
    
    # 3. Verify that 'hours ' does not trigger 'payment_request' (from ending in 'rs ')
    text_hours = "TRAI will deactivate your mobile number in 2 hours due to illegal activity."
    signals_hours = extract_signals(text_hours)
    assert "payment_request" not in signals_hours, f"Failed: 'hours ' matched payment_request. Signals: {signals_hours}"
    assert "urgent_deadline" in signals_hours, "Failed: urgent_deadline not detected"
    print("  [OK] Plural words ending in 'rs' (hours) exclusion test passed.")
    
    # 4. Verify that normal verbs like 'apply' do NOT trigger 'payment_request'
    text_apply = "Apply at this link before March 31."
    signals_apply = extract_signals(text_apply)
    assert "payment_request" not in signals_apply, f"Failed: 'apply' matched payment_request. Signals: {signals_apply}"
    print("  [OK] 'apply' exclusion test passed.")

def test_rule_layer_true_positives():
    print("\nRunning rule layer true positive tests...")
    
    # 1. Direct payment requests
    text_pay = "Pay Rs 500 processing fee to claim your prize."
    signals_pay = extract_signals(text_pay)
    assert "payment_request" in signals_pay, "Failed: Did not detect payment_request in text with 'Pay' and 'Rs'"
    assert "fake_reward" in signals_pay, "Failed: Did not detect fake_reward in lottery win context"
    print("  [OK] Direct payment request matched correctly.")
    
    # 2. Digital wallet payments
    text_crypto = "Send USDT to this wallet now."
    signals_crypto = extract_signals(text_crypto)
    assert "payment_request" in signals_crypto, "Failed: Did not detect payment_request for USDT wallet transfer"
    print("  [OK] Crypto wallet payment request matched correctly.")
    
    # 3. Authority threats
    text_threat = "Cybercrime Division has registered a case. Avoid arrest."
    signals_threat = extract_signals(text_threat)
    assert "authority_threat" in signals_threat, "Failed: Did not detect authority_threat"
    print("  [OK] Authority threats matched correctly.")

def test_risk_level_scoring():
    print("\nRunning risk level scoring tests...")
    
    # No flags
    assert get_risk_level_from_signals([]) == "low", "Failed: Empty signals should be low risk"
    
    # Medium flag (e.g. forward_pressure is not a high signal)
    assert get_risk_level_from_signals(["forward_pressure"]) == "medium", "Failed: Single low-threat signal should be medium risk"
    
    # High signal (e.g. payment_request)
    assert get_risk_level_from_signals(["payment_request"]) == "high", "Failed: Critical signal should be high risk"
    
    # 3 or more signals
    assert get_risk_level_from_signals(["forward_pressure", "urgent_deadline", "health_miracle"]) == "high", "Failed: 3 flags should trigger high risk"
    
    print("  [OK] Risk level scoring logic passed.")

def test_json_schema_validation():
    print("\nRunning JSON schema validation tests...")
    
    valid_output = {
        "input": "test claim text",
        "category": "scam",
        "risk_type": "kyc_scam",
        "risk_level": "high",
        "confidence_ceiling": "low",
        "risk_signals": ["urgent_deadline"],
        "evidence_needed": ["verification"],
        "recommended_action": "do not click",
        "uncertainty_note": "none"
    }
    
    # 1. Test standard valid object
    is_valid, err = validate(valid_output)
    assert is_valid, f"Failed: Valid JSON object rejected: {err}"
    print("  [OK] Valid JSON template passed schema validation.")
    
    # 2. Test missing required field
    invalid_missing = valid_output.copy()
    del invalid_missing["recommended_action"]
    is_valid, err = validate(invalid_missing)
    assert not is_valid, "Failed: Accepted JSON missing recommended_action"
    print("  [OK] Rejected JSON with missing required fields correctly.")
    
    # 3. Test invalid enum category value
    invalid_enum = valid_output.copy()
    invalid_enum["category"] = "unauthorized_category"
    is_valid, err = validate(invalid_enum)
    assert not is_valid, "Failed: Accepted unauthorized category value"
    print("  [OK] Rejected JSON with illegal enum value correctly.")

if __name__ == "__main__":
    print("=" * 50)
    print("DAM CLASSIFIER - AUTOMATED UNIT TESTS")
    print("=" * 50)
    try:
        test_rule_layer_false_positives()
        test_rule_layer_true_positives()
        test_risk_level_scoring()
        test_json_schema_validation()
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        print("=" * 50)
        sys.exit(1)