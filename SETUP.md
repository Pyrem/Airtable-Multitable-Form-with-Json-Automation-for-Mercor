# Setup and Usage Guide

This guide provides step-by-step instructions for setting up and using the Airtable Multi-Table Form Automation system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Airtable Configuration](#airtable-configuration)
4. [Environment Configuration](#environment-configuration)
5. [Usage](#usage)
6. [Customization](#customization)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- An Airtable account with a configured base (see [AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md))
- API key for at least one LLM provider (OpenAI, Anthropic, or Google Gemini)
- Basic knowledge of command-line operations

## Installation

### 1. Clone or Download the Repository

```bash
cd /path/to/Airtable-Multitable-Form-with-Json-Automation-for-Mercor
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Airtable Configuration

### 1. Create Your Airtable Base

Follow the instructions in [AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md) to set up your base with all required tables and fields.

### 2. Get Your Airtable API Key

1. Visit [https://airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Click "Create new token"
3. Name your token (e.g., "Applicant Automation")
4. Add the following scopes:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
5. Add access to your specific base
6. Click "Create token" and copy it

### 3. Get Your Base ID

1. Visit [https://airtable.com/api](https://airtable.com/api)
2. Click on your base
3. Copy the Base ID from the URL or the introduction section (starts with "app...")

## Environment Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Your .env File

Edit the `.env` file with your credentials:

```bash
# Required: Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_base_id_here

# Required: Choose ONE LLM provider and add its API key
LLM_PROVIDER=openai  # Options: openai, anthropic, gemini

# For OpenAI
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4

# For Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
# LLM_MODEL=claude-3-5-sonnet-20241022

# For Google Gemini
# GEMINI_API_KEY=...
# LLM_MODEL=gemini-pro

# Optional: Customize these if needed
MAX_TOKENS_PER_CALL=1000
MAX_RETRIES=3
MAX_HOURLY_RATE=100
MIN_AVAILABILITY_HOURS=20
MIN_YEARS_EXPERIENCE=4
```

### 3. Configure Shortlist Criteria (Optional)

The following environment variables control shortlist criteria:

```bash
# Tier-1 companies (comma-separated)
TIER_1_COMPANIES=Google,Meta,OpenAI,Microsoft,Amazon,Apple,Netflix,Anthropic

# Compensation criteria
MAX_HOURLY_RATE=100
MIN_AVAILABILITY_HOURS=20

# Experience criteria
MIN_YEARS_EXPERIENCE=4

# Location criteria (comma-separated)
APPROVED_LOCATIONS=US,USA,United States,Canada,UK,United Kingdom,Germany,India
```

## Usage

### Complete Pipeline (Recommended)

Run the entire pipeline for all applicants:

```bash
python run_pipeline.py --all
```

Run the pipeline for a specific applicant:

```bash
python run_pipeline.py --applicant-id rec1234567890
```

Force LLM re-evaluation:

```bash
python run_pipeline.py --all --force-llm
```

### Individual Scripts

#### 1. JSON Compression

Compress data from multiple tables into a single JSON object:

```bash
# Compress all applicants
python compress_json.py --all

# Compress specific applicant
python compress_json.py --applicant-id rec1234567890
```

#### 2. JSON Decompression

Decompress JSON back to normalized tables (for editing):

```bash
# Decompress all applicants
python decompress_json.py --all

# Decompress specific applicant
python decompress_json.py --applicant-id rec1234567890
```

#### 3. Lead Shortlisting

Evaluate applicants against criteria and create shortlisted leads:

```bash
# Process all applicants
python shortlist_leads.py --all

# Process specific applicant
python shortlist_leads.py --applicant-id rec1234567890
```

#### 4. LLM Evaluation

Evaluate applicants using LLM and add summaries, scores, and follow-up questions:

```bash
# Evaluate all applicants
python llm_evaluation.py --all

# Evaluate specific applicant
python llm_evaluation.py --applicant-id rec1234567890

# Force re-evaluation
python llm_evaluation.py --all --force
```

## Workflow

### Typical Workflow for New Applicants

1. **Applicant submits three forms** (Personal Details, Work Experience, Salary Preferences)
2. **Run compression** to create the JSON object:
   ```bash
   python compress_json.py --applicant-id rec1234567890
   ```
3. **Run shortlist evaluation**:
   ```bash
   python shortlist_leads.py --applicant-id rec1234567890
   ```
4. **Run LLM evaluation**:
   ```bash
   python llm_evaluation.py --applicant-id rec1234567890
   ```

Or simply run:
```bash
python run_pipeline.py --applicant-id rec1234567890
```

### Workflow for Editing Applicant Data

1. **Edit the Compressed JSON** directly in Airtable, OR
2. **Decompress to tables**:
   ```bash
   python decompress_json.py --applicant-id rec1234567890
   ```
3. **Edit the individual table records** in Airtable
4. **Re-compress**:
   ```bash
   python compress_json.py --applicant-id rec1234567890
   ```
5. **Re-run evaluation**:
   ```bash
   python run_pipeline.py --applicant-id rec1234567890 --force-llm
   ```

## Customization

### Modifying Shortlist Criteria

Edit the `.env` file to adjust criteria:

```bash
# Example: Change max hourly rate to $120
MAX_HOURLY_RATE=120

# Example: Add more Tier-1 companies
TIER_1_COMPANIES=Google,Meta,OpenAI,Microsoft,Amazon,Apple,Netflix,Anthropic,DeepMind,Stripe
```

For more complex criteria changes, edit the functions in `shortlist_leads.py`:
- `check_experience_criteria()`
- `check_compensation_criteria()`
- `check_location_criteria()`

### Customizing LLM Prompts

Edit the `build_evaluation_prompt()` function in `llm_evaluation.py` to change what the LLM evaluates.

Example modifications:
```python
def build_evaluation_prompt(compressed_json: str) -> str:
    prompt = f"""You are a recruiting analyst specializing in software engineering roles.

    Evaluate this candidate profile focusing on:
    1. Technical depth and breadth
    2. Leadership experience
    3. Cultural fit indicators

    ... (rest of prompt)
    """
    return prompt
```

### Adding New LLM Providers

To add a new LLM provider:

1. Install the SDK: `pip install new-llm-sdk`
2. Add configuration to `config.py`
3. Add a new method in `llm_evaluation.py`:
   ```python
   def _call_new_provider(self, prompt: str) -> Optional[str]:
       # Implementation
   ```
4. Update the `call_llm()` method to handle the new provider

### Extending the JSON Schema

To add new fields to the compressed JSON:

1. Add the field to the appropriate Airtable table
2. Update `compress_json.py` to include the new field in the JSON structure
3. Update `decompress_json.py` to handle the new field when decompressing

## Troubleshooting

### Common Issues

#### "Configuration errors: AIRTABLE_API_KEY is required"

**Solution**: Make sure you've created a `.env` file and added your Airtable API key.

#### "Error retrieving applicant: 404"

**Solution**: Check that:
- The applicant ID is correct
- Your API token has access to the base
- The base ID in `.env` is correct

#### "LLM API call failed"

**Solution**:
- Verify your LLM API key is correct and active
- Check your API usage limits and billing
- Ensure you have the correct model name in `.env`

#### "ModuleNotFoundError"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

#### Rate Limiting Issues

**Solution**: The scripts include retry logic with exponential backoff. If you're still hitting limits:
- Reduce the frequency of API calls
- Add delays between processing applicants
- Contact your LLM provider to increase limits

### Debugging

Enable debug logging by editing any script and changing:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

### Getting Help

1. Check the logs for detailed error messages
2. Review the [AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md) to ensure your base is set up correctly
3. Verify your `.env` configuration matches `.env.example`
4. Test with a single applicant before processing all applicants

## Best Practices

1. **Test with sample data first** before processing real applicants
2. **Backup your Airtable base** before running bulk operations
3. **Run scripts during off-peak hours** to avoid rate limiting
4. **Monitor API costs** especially for LLM calls
5. **Version control your .env file** (but never commit it to Git)
6. **Use the pipeline script** for consistent results
7. **Review LLM outputs** periodically to ensure quality

## Security Notes

- Never commit your `.env` file to version control
- Rotate API keys periodically
- Use minimal scopes for Airtable tokens
- Store credentials securely
- Monitor API usage for unusual activity
