import json
import time
import os
import re
from datetime import datetime
from collections import Counter
from rules import extract_signals, get_risk_level_from_signals
from llm_classifier import classify
from validator import validate

def generate_fallback(text: str, signals: list, rule_risk: str, error_msg: str) -> dict:
    """
    If the LLM classifier is down or API limits are hit, we don't want the whole run
    to crash. This function acts as a smart fallback to generate schema-compliant JSON.
    It uses simple heuristics on the input text to assign the category and risk type.
    """
    category = "ambiguous"
    risk_type = "ambiguous_claim"
    
    text_lower = text.lower()
    
    # Categorization heuristic: deduce category from rule risk and key text phrases
    if rule_risk == "high":
        category = "scam"
        if "kyc" in text_lower:
            risk_type = "kyc_scam"
        elif "won" in text_lower or "congratulations" in text_lower or "prize" in text_lower:
            risk_type = "fake_reward"
        elif "invest" in text_lower or "deposit" in text_lower or "crypto" in text_lower:
            risk_type = "investment_scam"
        else:
            risk_type = "authority_impersonation"
    elif rule_risk == "medium":
        category = "misinformation"
        if "cure" in text_lower or "cancer" in text_lower or "remedy" in text_lower or "prevent" in text_lower:
            risk_type = "health_misinformation"
        elif "hack" in text_lower or "election" in text_lower or "evm" in text_lower:
            risk_type = "political_rumor"
        elif "whatsapp" in text_lower or "forward" in text_lower:
            risk_type = "social_viral"
        else:
            risk_type = "tech_misinformation"
    elif rule_risk == "low":
        category = "safe"
        risk_type = "safe_factual"

    return {
        "input": text,
        "category": category,
        "risk_type": risk_type,
        "risk_level": rule_risk,
        "confidence_ceiling": "low",
        "risk_signals": signals if signals else ["failed_classification_fallback"],
        "evidence_needed": ["manual verification required due to api classification failure"],
        "recommended_action": "verify information manually before taking action",
        "uncertainty_note": f"classification fallback triggered: {error_msg}"
    }

def update_evaluation_report(summary_text: str):
    """
    Appends or replaces the ## Evaluation Summary section in evaluation_report.md
    with the metrics calculated during this run. This makes it easy to keep our
    documentation in lockstep with our code runs.
    """
    report_path = "evaluation_report.md"
    if not os.path.exists(report_path):
        return
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    marker = "## Evaluation Summary"
    if marker in content:
        # If the summary is already there, strip it out and overwrite with the new one
        parts = content.split(marker)
        content = parts[0] + marker + "\n\n" + summary_text + "\n"
    else:
        # Otherwise, simply append to the end of the file
        content = content.strip() + "\n\n" + marker + "\n\n" + summary_text + "\n"
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

def run_pipeline(input_file: str, output_file: str, failure_log_file: str = "data/failures.log"):
    """
    Main orchestration routine. Reads input claims, coordinates the rules-based pre-screening,
    queries the LLM classifier (with retries), validates structural integrity, and saves outputs.
    """
    # Create the output directories if they aren't already present
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(os.path.dirname(failure_log_file), exist_ok=True)

    with open(input_file, encoding="utf-8") as f:
        inputs = json.load(f)
    
    results = []
    failures_occurred = []
    
    # Optimization: If we detect that the user's API key is invalid or unauthorized,
    # we set this flag to True so we don't spend 2 minutes waiting for subsequent rows
    # to fail. We fail fast and use fallbacks instantly.
    api_auth_failed = False
    
    for item in inputs:
        text = item["text"]
        item_id = item["id"]
        print(f"Processing ID {item_id}...")
        
        # 1. Run deterministic rules layer first
        signals = extract_signals(text)
        rule_risk = get_risk_level_from_signals(signals)
        
        output = None
        error_msg = ""
        
        # 2. Query LLM classifier
        if api_auth_failed:
            error_msg = "Skipped LLM query due to previous API authentication failure."
            output = generate_fallback(text, signals, rule_risk, error_msg)
        else:
            # Try up to 3 times in case of transient API hiccup or rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    output = classify(text, signals)
                    # Run schema validator on LLM output
                    is_valid, err = validate(output)
                    if not is_valid:
                        raise ValueError(f"JSON validation failed: {err}")
                    break  # Got valid output, stop retrying
                except Exception as e:
                    error_str = str(e)
                    print(f"  Attempt {attempt + 1} failed: {error_str}")
                    
                    # Detect API key auth failures or hard zero-quota limits (limit: 0) to skip further calls
                    if "API key not valid" in error_str or "API_KEY_INVALID" in error_str or "INVALID_ARGUMENT" in error_str or "limit: 0" in error_str:
                        api_auth_failed = True
                        error_msg = f"API Quota/Auth Error: {error_str}"
                        break
                    
                    error_msg = error_str
                    if attempt < max_retries - 1:
                        # If it's a rate limit error, sleep longer (35s) to allow reset
                        if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower() or "429" in error_str:
                            sleep_time = 35
                            print(f"  Rate limit hit. Retrying in {sleep_time}s...")
                        else:
                            sleep_time = (attempt + 1) * 2
                            print(f"  Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
            
            # If all retries were exhausted, trigger the heuristic fallback
            if output is None:
                print(f"  [FALLBACK] LLM classification failed. Generating fallback output.")
                output = generate_fallback(text, signals, rule_risk, error_msg)
                
                # Append to failures log for transparency
                log_entry = f"[{datetime.now().isoformat()}] ID {item_id} failed: {error_msg}\n"
                failures_occurred.append({"id": item_id, "error": error_msg})
                with open(failure_log_file, "a", encoding="utf-8") as lf:
                    lf.write(log_entry)
        
        # 3. Add auxiliary validation and rule metadata fields
        is_valid, validation_error = validate(output)
        output["_rule_signals_detected"] = signals
        output["_rule_risk_level"] = rule_risk
        output["_validation"] = "pass" if is_valid else f"FAIL: {validation_error}"
        
        results.append(output)
        print(f"  [OK] Done")
        
        # 4. Respect Gemini API free-tier rate limits (approx 15 requests per minute)
        # We only sleep if we actually made a network call to the LLM.
        if not api_auth_failed:
            time.sleep(3)
    
    # Save results to output json file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # 5. Compute Evaluation Metrics for the summary section
    total_inputs = len(inputs)
    validation_pass_count = sum(1 for r in results if r["_validation"] == "pass")
    
    categories = Counter(r["category"] for r in results)
    
    # Calculate cases where the rules layer and LLM layer disagree on threat risk level.
    # This helps researchers identify patterns missed by the rules or LLM quirks.
    disagreement_count = 0
    disagreement_cases = []
    for i, r in enumerate(results):
        llm_risk = r["risk_level"]
        rule_risk = r["_rule_risk_level"]
        if llm_risk != rule_risk:
            disagreement_count += 1
            disagreement_cases.append({
                "id": inputs[i]["id"],
                "text": r["input"],
                "rule_risk": rule_risk,
                "llm_risk": llm_risk
            })
            
    # Compile failures/fallback descriptions
    failure_cases_desc = []
    if failures_occurred:
        for f in failures_occurred:
            failure_cases_desc.append(f"- ID {f['id']}: {f['error']}")
    else:
        failure_cases_desc.append("- No runtime classification/validation failures occurred in this run.")

    # Format evaluation markdown report text
    summary_parts = [
        f"- **Validation Pass Count**: {validation_pass_count}/{total_inputs} (All outputs are validated against the schema)",
        f"- **Category Distribution**:",
    ]
    for cat, count in categories.items():
        summary_parts.append(f"  - `{cat}`: {count}")
    
    summary_parts.append(f"- **Rule/LLM Disagreement Count**: {disagreement_count} cases")
    if disagreement_cases:
        for dc in disagreement_cases:
            summary_parts.append(f"  - Case ID {dc['id']}: Rule rated `{dc['rule_risk']}` | LLM rated `{dc['llm_risk']}`")
            
    summary_parts.append("- **Known Failure Cases / Fallbacks**:")
    summary_parts.extend(f"  {line}" for line in failure_cases_desc)
    
    summary_text = "\n".join(summary_parts)
    
    # Print summary to console for immediate visibility
    print("\n" + "="*40 + "\nEVALUATION SUMMARY\n" + "="*40)
    print(summary_text)
    print("="*40 + "\n")
    
    # Dynamically append or replace the metrics in evaluation_report.md
    update_evaluation_report(summary_text)
    print(f"Evaluation report updated. Results written to {output_file}.")

if __name__ == "__main__":
    run_pipeline("data/inputs.json", "data/outputs.json")