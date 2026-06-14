# DAM Trust Signal Classifier — Evaluation Report

## What categories did you define and why?
Four categories: scam, misinformation, ambiguous, safe.

- scam: messages with clear financial or identity harm intent
- misinformation: false factual claims without direct financial motive
- ambiguous: insufficient signals to confirm or deny — treated conservatively
- safe: verifiable low-risk factual content used as control cases

These four cover the full spectrum DAM encounters without over-fragmenting 
the taxonomy.

## What risk signals matter most for DAM?
In order of importance:
1. payment_request — strongest scam indicator, direct financial harm
2. authority_threat — high psychological pressure (police, court, Aadhaar)
3. suspicious_link — direct attack vector
4. urgent_deadline — present in nearly all scams to prevent rational thinking
5. forward_pressure — primary misinformation amplification mechanism
6. guaranteed_return — investment fraud marker
7. health_miracle — medical misinformation with real harm potential

## How did you prevent overconfident outputs?
Three mechanisms:
1. System prompt explicitly forbids confidence_ceiling: "high" for unverifiable claims
2. confidence_ceiling and risk_level are kept as separate fields — a claim can 
   be high risk but still have low confidence ceiling
3. LLM temperature set to 0.1 for consistency
4. Rule layer signals are passed as context, not as final labels — LLM makes 
   the final classification decision
5. Ambiguous claims default to low confidence ceiling by design

## How would this fail in real-world use?
1. Hindi/Hinglish messages — rule layer keywords are English only, will miss 
   signals in regional language scams
2. Adversarial phrasing — scammers who deliberately avoid trigger words will 
   bypass the rule layer
3. Legitimate urgency — real bank alerts and government notices may be 
   misclassified as scams
4. Satire and parody — may be classified as misinformation
5. LLM inconsistency — same input can produce slightly different outputs 
   across runs due to model variability
6. New scam patterns — rule layer needs manual updates as scam tactics evolve

## How would you improve this with real DAM claim logs?
1. Extract actual signal patterns from confirmed scam cases to improve rules.py
2. Build a feedback loop: human review → label corrections → prompt refinement
3. Add multilingual rule layer for Hindi, Tamil, Bengali, Marathi
4. Fine-tune confidence thresholds based on false positive/negative rates
5. Add a disagreement flag when rule layer and LLM risk levels conflict

## What should be manually reviewed before production?
1. All ambiguous_claim outputs — by definition unresolved
2. Cases where _rule_risk_level and LLM risk_level disagree
3. All health_misinformation outputs — highest real-world harm potential
4. All political_rumor outputs — sensitive and legally complex
5. Any output with confidence_ceiling: low

## Prompt-only vs Hybrid recommendation?
Hybrid is recommended for DAM at this stage. Reasons:

- Rule layer catches obvious cases without API call — reduces cost at scale
- Hybrid gives explainability: you can show users which specific signal 
  triggered the flag
- Prompt-only risks overconfidence without a grounding layer
- However, prompt-only is easier to iterate on early — if DAM needs to 
  move fast, a well-engineered prompt-only system is better than a poorly 
  implemented hybrid

As DAM scales and real claim logs become available, the rule layer should 
be replaced with a trained signal extractor fine-tuned on actual data.