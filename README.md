# DAM Trust Signal Classifier

A hybrid classifier for DAM (Defence Against Misinformation) that analyzes 
risky claims and returns structured JSON risk analysis.

## Approach
Option B — Hybrid: deterministic rule layer + LLM classification.

## Setup
pip install google-genai jsonschema python-dotenv
Add GEMINI_API_KEY to .env file

## Run
python pipeline.py

## Architecture
Rule layer (rules.py) → extracts signals, estimates risk level
LLM layer (llm_classifier.py) → classifies with full schema
Validator (validator.py) → ensures JSON schema compliance
Pipeline (pipeline.py) → orchestrates all three

## Limitations
- English-only rule signals
- Not production-ready
- Requires human review for ambiguous outputs