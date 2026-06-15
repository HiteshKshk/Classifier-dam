# DAM Trust Signal Classifier

A hybrid classifier for DAM (Defence Against Misinformation) that combines a deterministic rule-based pre-screening layer and an LLM classification layer to analyze potentially risky claims and return structured JSON risk analyses.

## Core Features

- **Hybrid Detection**: Rule-based screening catches obvious scam patterns (e.g. key threat signals) without requiring LLM calls, providing speed and low cost at scale. The LLM layer acts as the final decision maker, providing schema-compliant JSON analysis.
- **Improved Rule Logic**: Avoids false positives (e.g., words like `paytm` or `apply` triggering `payment_request` flags) by implementing regular expression keyword matching with word boundaries.
- **Robust Pipeline**: Includes automatic API retry logic (up to 3 times) and a schema-compliant fallback output mechanism so that all input examples generate outputs even during API or safety-blocking issues.
- **Failure Logging**: All runtime classification failures are logged to `data/failures.log`.
- **Dynamic Summaries**: Automatically generates metrics for validation rates, classification category breakdowns, and rule/LLM disagreement details.

---

## Setup Instructions

### 1. Prerequisite
Ensure you have **Python 3.10 or higher** installed.

### 2. Install Dependencies
Install all required libraries using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your actual Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

*(Note: `.env` is ignored by Git in `.gitignore` to prevent leaking credentials.)*

---

## Running the Pipeline

To run the classifier on the inputs in `data/inputs.json` and generate the `data/outputs.json` file, run:
```bash
python classifier/pipeline.py
```

### Output Validation
All classified entries are validated against the schema defined in `classifier/validator.py` before being saved. If a row fails to classify via the LLM, the pipeline logs the failure to `data/failures.log` and automatically falls back to a schema-compliant rule-based evaluation, ensuring 100% output consistency.

---

## Project Structure
- `classifier/rules.py`: Regex pattern matching for rule-based signal pre-screening and initial risk calculation.
- `classifier/llm_classifier.py`: Interaction wrapper for Gemini LLM, configures safety thresholds to `BLOCK_NONE`, and normalizes output formatting.
- `classifier/validator.py`: JSON schema validator verifying structural and value compliance.
- `classifier/pipeline.py`: Main orchestrator script reading input, executing classifications, tracking metrics, and writing outputs/logs.
- `data/inputs.json`: Contains 20 evaluation claims.
- `data/outputs.json`: Stores output results for all 20 inputs.
- `data/failures.log`: Text file logging any classification errors.
- `evaluation_report.md`: Document describing taxonomy, risks, failure modes, and automated run metrics.