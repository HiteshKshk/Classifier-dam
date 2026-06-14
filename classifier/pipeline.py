import json
import time
from collections import Counter
from rules import extract_signals, get_risk_level_from_signals
from llm_classifier import classify
from validator import validate

def run_pipeline(input_file: str, output_file: str):
    with open(input_file) as f:
        inputs = json.load(f)
    
    results = []
    failed = []
    
    for item in inputs:
        text = item["text"]
        print(f"Processing ID {item['id']}...")
        
        signals = extract_signals(text)
        rule_risk = get_risk_level_from_signals(signals)
        
        try:
            output = classify(text, signals)
            is_valid, error = validate(output)
            output["_rule_signals_detected"] = signals
            output["_rule_risk_level"] = rule_risk
            output["_validation"] = "pass" if is_valid else f"FAIL: {error}"
            results.append(output)
            print(f"  ✓ Done")
            
        except Exception as e:
            failed.append({"id": item["id"], "error": str(e)})
            print(f"  FAILED: {e}")
        
        time.sleep(5)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    categories = Counter(r["category"] for r in results)
    print("\nCategory breakdown:", dict(categories))

    print(f"\nDone. {len(results)} classified, {len(failed)} failed.")
    if failed:
        print("Failed:", failed)

if __name__ == "__main__":
    run_pipeline("data/inputs.json", "data/outputs.json")