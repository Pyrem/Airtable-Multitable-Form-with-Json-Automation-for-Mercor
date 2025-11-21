# CLAUDE.md - AI Assistant Guide

This document provides comprehensive information about the codebase structure, development workflows, and key conventions for AI assistants working with this project.

## Project Overview

This is the **Airtable Multi-Table Form + JSON Automation** system, designed for the Mercor Mini-Interview Task. It automates the collection, processing, and evaluation of contractor applications using:

- **Airtable** as the data store with a multi-table normalized schema
- **Python scripts** for data compression, decompression, and automation
- **LLM APIs** (OpenAI, Anthropic, or Gemini) for intelligent evaluation

### Business Logic

1. **Data Collection**: Applicants submit information via three separate Airtable forms (Personal Details, Work Experience, Salary Preferences)
2. **Data Compression**: Python scripts gather data from linked tables and compress into a single JSON object
3. **Lead Shortlisting**: Automated evaluation against multi-factor rules (experience, compensation, location)
4. **LLM Enrichment**: AI-powered evaluation providing summaries, quality scores, and follow-up questions
5. **Data Decompression**: Ability to expand JSON back to normalized tables for editing

## Repository Structure

```
/
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git ignore file
├── README.md                   # Project README
├── CLAUDE.md                   # This file - AI assistant guide
├── SETUP.md                    # Setup and usage documentation
├── AIRTABLE_SCHEMA.md          # Detailed Airtable schema documentation
├── requirements.txt            # Python dependencies
│
├── config.py                   # Configuration management and validation
├── airtable_utils.py           # Airtable API wrapper and utilities
│
├── compress_json.py            # Script: Multi-table to JSON compression
├── decompress_json.py          # Script: JSON to multi-table decompression
├── shortlist_leads.py          # Script: Rule-based lead shortlisting
├── llm_evaluation.py           # Script: LLM-based evaluation and enrichment
├── run_pipeline.py             # Master orchestrator script
│
└── .git/                       # Git repository
```

## Core Components

### 1. Configuration System (config.py)

**Purpose**: Centralized configuration management with environment variable loading and validation.

**Key Features**:
- Loads from `.env` file using `python-dotenv`
- Validates required configurations before execution
- Provides type-safe access to settings
- Supports multiple LLM providers

**Key Classes**:
- `Config`: Static configuration class with validation methods

**Usage Pattern**:
```python
from config import Config

Config.validate()  # Always validate first
api_key = Config.AIRTABLE_API_KEY
```

**Important Fields**:
- Airtable: `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`
- LLM: `LLM_PROVIDER`, `LLM_MODEL`, provider-specific API keys
- Criteria: `TIER_1_COMPANIES`, `MAX_HOURLY_RATE`, `MIN_AVAILABILITY_HOURS`, etc.

### 2. Airtable Utilities (airtable_utils.py)

**Purpose**: Abstraction layer over the Airtable API for cleaner, reusable data access.

**Key Features**:
- Initializes table references
- CRUD operations for all tables
- Formula-based querying
- Error handling and logging

**Key Class**:
- `AirtableClient`: Main client class wrapping pyairtable API

**Key Methods**:
```python
client = AirtableClient()
client.get_applicant(applicant_id)
client.get_personal_details(applicant_id)
client.get_work_experiences(applicant_id)
client.update_applicant(applicant_id, fields)
client.create_shortlisted_lead(fields)
```

**Conventions**:
- All methods include error handling
- Methods return `None` on failure
- Methods log operations at INFO level
- Uses Airtable formulas for filtering linked records

### 3. JSON Compression (compress_json.py)

**Purpose**: Aggregates data from multiple linked tables into a single JSON object.

**Key Functions**:
- `compress_applicant_data()`: Fetches and structures data
- `calculate_total_experience()`: Computes total years of experience
- `update_compressed_json()`: Writes JSON to Applicants table
- `compress_all_applicants()`: Batch processing

**JSON Schema**:
```json
{
  "personal": {
    "name": "string",
    "email": "string",
    "location": "string",
    "linkedin": "string"
  },
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "technologies": "string",
      "description": "string"
    }
  ],
  "total_experience_years": 0.0,
  "salary": {
    "preferred_rate": 0,
    "minimum_rate": 0,
    "currency": "USD",
    "availability": 0
  }
}
```

**Usage**:
```bash
python compress_json.py --applicant-id rec123
python compress_json.py --all
```

### 4. JSON Decompression (decompress_json.py)

**Purpose**: Reads Compressed JSON and updates child tables to match, enabling JSON-based editing.

**Key Functions**:
- `decompress_applicant_data()`: Main decompression logic
- `upsert_personal_details()`: Update or create personal details
- `upsert_work_experiences()`: Update/create/delete work records to match JSON
- `upsert_salary_preferences()`: Update or create salary preferences

**Important Logic**:
- **Upsert pattern**: Updates existing records or creates new ones
- **Work experience deletion**: Removes records not present in JSON
- **Index-based matching**: Matches work experiences by position in array

**Usage**:
```bash
python decompress_json.py --applicant-id rec123
python decompress_json.py --all
```

### 5. Lead Shortlisting (shortlist_leads.py)

**Purpose**: Automated evaluation against multi-factor business rules to identify promising candidates.

**Shortlist Criteria** (all must pass):

1. **Experience**:
   - `>= 4 years total experience` OR
   - `Worked at a Tier-1 company` (Google, Meta, OpenAI, etc.)

2. **Compensation**:
   - `Preferred Rate <= $100/hour` AND
   - `Availability >= 20 hours/week`

3. **Location**:
   - In approved countries: US, Canada, UK, Germany, India

**Key Functions**:
- `evaluate_applicant()`: Runs all criteria checks
- `check_experience_criteria()`: Experience validation
- `check_compensation_criteria()`: Compensation validation
- `check_location_criteria()`: Location validation
- `create_shortlisted_lead()`: Creates lead record if all criteria pass

**Output**:
- Updates `Shortlist Status` field in Applicants table
- Creates record in Shortlisted Leads table with score reasoning

**Usage**:
```bash
python shortlist_leads.py --applicant-id rec123
python shortlist_leads.py --all
```

### 6. LLM Evaluation (llm_evaluation.py)

**Purpose**: Uses LLM APIs to provide qualitative evaluation, summaries, and recommendations.

**Key Features**:
- Multi-provider support (OpenAI, Anthropic, Gemini)
- Exponential backoff retry logic
- Structured prompt engineering
- Response parsing with regex

**Key Classes**:
- `LLMEvaluator`: Wrapper for LLM API calls with retry logic

**Key Functions**:
- `build_evaluation_prompt()`: Constructs the LLM prompt
- `parse_llm_response()`: Extracts structured data from LLM output
- `evaluate_applicant_with_llm()`: Complete evaluation workflow

**LLM Prompt Structure**:
```
You are a recruiting analyst. Given this JSON applicant profile, do four things:

1. Provide a concise 75-word summary of the candidate.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.
```

**Expected Response Format**:
```
Summary: <75-word summary>
Score: <1-10>
Issues: <comma-separated issues or 'None'>
Follow-Ups:
- <question 1>
- <question 2>
- <question 3>
```

**Safety Features**:
- Rate limiting protection with delays
- Token budget controls
- Skip re-evaluation unless forced
- Error logging and retry with exponential backoff

**Usage**:
```bash
python llm_evaluation.py --applicant-id rec123
python llm_evaluation.py --all
python llm_evaluation.py --all --force  # Re-evaluate all
```

### 7. Pipeline Orchestrator (run_pipeline.py)

**Purpose**: Master script that runs the complete workflow in the correct order.

**Pipeline Steps**:
1. Compress data to JSON
2. Evaluate for shortlisting
3. Run LLM evaluation

**Key Functions**:
- `run_pipeline_for_applicant()`: Single applicant pipeline
- `run_pipeline_for_all()`: Batch processing pipeline

**Usage**:
```bash
python run_pipeline.py --applicant-id rec123
python run_pipeline.py --all
python run_pipeline.py --all --force-llm
```

## Development Workflows

### Adding a New Feature

1. **Identify the component** (compression, shortlisting, LLM, etc.)
2. **Update the relevant script** with new logic
3. **Update config.py** if new settings are needed
4. **Update .env.example** with new environment variables
5. **Test with a single applicant** before batch processing
6. **Update documentation** (this file, SETUP.md, AIRTABLE_SCHEMA.md)

### Modifying Shortlist Criteria

**File**: `shortlist_leads.py`

**Steps**:
1. Edit the check functions:
   - `check_experience_criteria()`
   - `check_compensation_criteria()`
   - `check_location_criteria()`
2. Update `config.py` if adding new configurable values
3. Update `.env.example` with new variables
4. Document changes in SETUP.md

**Example** - Add skill requirement:
```python
def check_skills_criteria(compressed_data: Dict[str, Any]) -> tuple[bool, str]:
    """Check if applicant has required skills."""
    required_skills = Config.REQUIRED_SKILLS
    experiences = compressed_data.get('experience', [])

    for exp in experiences:
        technologies = exp.get('technologies', '').lower()
        for skill in required_skills:
            if skill.lower() in technologies:
                return True, f"Has required skill: {skill}"

    return False, "Missing required skills"
```

### Customizing LLM Prompts

**File**: `llm_evaluation.py`

**Function**: `build_evaluation_prompt()`

**Guidelines**:
- Keep prompts concise and specific
- Use structured output format
- Test with multiple applicants to ensure consistency
- Include examples in the prompt if needed

**Example**:
```python
def build_evaluation_prompt(compressed_json: str) -> str:
    prompt = f"""You are a senior technical recruiter specializing in AI/ML roles.

    Evaluate this candidate focusing on:
    - Depth of machine learning experience
    - Publications or open-source contributions
    - Research background

    Candidate Profile:
    ```json
    {compressed_json}
    ```

    Provide your evaluation in this format:
    Summary: <75 words>
    Score: <1-10>
    ML Experience Level: <Junior/Mid/Senior/Expert>
    Red Flags: <list or 'None'>
    """
    return prompt
```

### Adding a New LLM Provider

**File**: `llm_evaluation.py`, `config.py`

**Steps**:

1. **Install SDK**:
```bash
pip install new-provider-sdk
echo "new-provider-sdk==x.y.z" >> requirements.txt
```

2. **Add to config.py**:
```python
class Config:
    # ...
    NEWPROVIDER_API_KEY: str = os.getenv('NEWPROVIDER_API_KEY', '')
```

3. **Add method to LLMEvaluator**:
```python
def _call_newprovider(self, prompt: str) -> Optional[str]:
    """Call NewProvider API."""
    try:
        import newprovider
        client = newprovider.Client(api_key=Config.NEWPROVIDER_API_KEY)
        response = client.generate(prompt=prompt, max_tokens=self.max_tokens)
        return response.text
    except Exception as e:
        logger.error(f"NewProvider API error: {e}")
        return None
```

4. **Update call_llm()**:
```python
def call_llm(self, prompt: str) -> Optional[str]:
    # ...
    elif self.provider == 'newprovider':
        response = self._call_newprovider(prompt)
    # ...
```

### Extending the JSON Schema

**Files**: `compress_json.py`, `decompress_json.py`

**Steps**:

1. **Add field to Airtable** (e.g., "References" table)

2. **Update compression**:
```python
def compress_applicant_data(client: AirtableClient, applicant_id: str):
    # ...
    references = client.get_references(applicant_id)
    if references:
        compressed_data['references'] = [
            {
                'name': ref.get('fields', {}).get('Name', ''),
                'email': ref.get('fields', {}).get('Email', ''),
                'relationship': ref.get('fields', {}).get('Relationship', '')
            }
            for ref in references
        ]
    # ...
```

3. **Update decompression**:
```python
def upsert_references(client: AirtableClient, applicant_id: str, references_data: List[Dict]):
    # Similar to upsert_work_experiences
    # ...
```

4. **Update airtable_utils.py**:
```python
class AirtableClient:
    def __init__(self):
        # ...
        self.references = self.base.table('References')

    def get_references(self, applicant_id: str) -> List[Dict[str, Any]]:
        # ...
```

## Key Conventions

### Code Style

- **Python Version**: 3.8+
- **Style Guide**: PEP 8
- **Docstrings**: Google style
- **Type Hints**: Used throughout for function signatures
- **Line Length**: 100 characters maximum

### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Files**: `snake_case.py`

### Error Handling

- All Airtable operations wrapped in try-except
- Functions return `None` on failure, not raising exceptions
- All errors logged with `logger.error()`
- Retry logic for LLM API calls (exponential backoff)

### Logging

- **Level**: INFO by default
- **Format**: `%(asctime)s - %(levelname)s - %(message)s`
- **Usage**:
  - `logger.info()` for normal operations
  - `logger.warning()` for missing data
  - `logger.error()` for failures

### Testing Approach

When testing changes:

1. **Test with single applicant first**:
   ```bash
   python script.py --applicant-id rec_test_123
   ```

2. **Verify in Airtable** that changes are correct

3. **Test with small batch** before processing all:
   ```bash
   # Manually limit in code or filter in Airtable
   ```

4. **Always backup data** before bulk operations

### Environment Variables

- **Never commit** `.env` file
- **Always update** `.env.example` when adding new variables
- **Use sensible defaults** in `config.py` where appropriate
- **Validate required variables** in `Config.validate()`

### Airtable Conventions

- **Field Names**: Title Case, no emojis
- **Table Names**: Title Case, no emojis
- **Date Format**: YYYY-MM-DD
- **Record IDs**: Always use linked record fields, never hardcode IDs
- **Formulas**: Link to Applicants table from all child tables

## Common Patterns

### Airtable Record Processing

```python
def process_applicant(client: AirtableClient, applicant_id: str) -> bool:
    """Standard pattern for processing an applicant."""
    logger.info(f"Processing applicant {applicant_id}")

    try:
        # 1. Get applicant record
        applicant = client.get_applicant(applicant_id)
        if not applicant:
            logger.error(f"Applicant {applicant_id} not found")
            return False

        # 2. Extract fields
        fields = applicant.get('fields', {})

        # 3. Process data
        # ... your logic ...

        # 4. Update record
        result = client.update_applicant(applicant_id, {
            'Field Name': 'value'
        })

        if result:
            logger.info(f"Successfully processed {applicant_id}")
            return True
        else:
            logger.error(f"Failed to update {applicant_id}")
            return False

    except Exception as e:
        logger.error(f"Error processing {applicant_id}: {e}")
        return False
```

### Batch Processing

```python
def process_all_applicants(client: AirtableClient) -> None:
    """Standard pattern for batch processing."""
    logger.info("Processing all applicants")

    applicants = client.get_all_applicants()
    logger.info(f"Found {len(applicants)} applicants")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        applicant_id = applicant['id']
        if process_applicant(client, applicant_id):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Complete: {success_count} successful, {failure_count} failed")
```

### CLI Argument Parsing

```python
def main():
    """Standard pattern for CLI scripts."""
    import argparse

    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('--applicant-id', type=str, help='Specific applicant ID')
    parser.add_argument('--all', action='store_true', help='Process all applicants')
    parser.add_argument('--force', action='store_true', help='Force re-processing')

    args = parser.parse_args()

    client = AirtableClient()

    if args.applicant_id:
        # Single processing
        success = process_applicant(client, args.applicant_id)
        print(f"{'Success' if success else 'Failed'}")
    elif args.all:
        # Batch processing
        process_all_applicants(client)
    else:
        print("Please specify --applicant-id or --all")
        parser.print_help()

if __name__ == '__main__':
    main()
```

## Security Considerations

### API Key Management

- Store in `.env` file only
- Never log API keys
- Use environment-specific keys (dev/prod)
- Rotate keys periodically

### Airtable Permissions

- Use minimal required scopes
- Create separate tokens per environment
- Audit token usage regularly

### LLM API Security

- Monitor token usage and costs
- Set budget guardrails
- Validate/sanitize all inputs
- Don't send PII unless necessary

### Data Privacy

- Applicant data may contain PII
- Ensure compliance with data protection regulations
- Implement data retention policies
- Secure backup procedures

## Troubleshooting Guide

### Common Issues

1. **Import Errors**:
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **Airtable API Errors**:
   - Verify API key and base ID in `.env`
   - Check token scopes and permissions
   - Confirm table names match exactly

3. **LLM API Failures**:
   - Check API key validity
   - Verify billing/credits available
   - Check model name is correct
   - Review rate limits

4. **JSON Parse Errors**:
   - Validate JSON structure in Airtable
   - Check for special characters
   - Ensure proper escaping

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Changes

1. Create test applicant record
2. Run script with `--applicant-id`
3. Check results in Airtable
4. Review logs for errors

## Performance Considerations

### Rate Limiting

- Airtable: 5 requests/second per base
- OpenAI: Varies by tier
- Anthropic: Varies by tier
- Gemini: Varies by tier

**Mitigation**:
- Add delays between requests
- Implement retry with backoff
- Process in smaller batches

### Optimization Tips

1. **Batch API calls** when possible
2. **Cache applicant records** to avoid redundant fetches
3. **Use filters** to process only updated records
4. **Parallel processing** for independent operations
5. **Monitor API costs** especially for LLM calls

## Future Enhancements

Potential improvements to consider:

1. **Webhook Integration**: Trigger automations on form submission
2. **Email Notifications**: Alert team when leads are shortlisted
3. **Dashboard**: Visual analytics for applicant pipeline
4. **Advanced Matching**: ML-based candidate-role matching
5. **Interview Scheduling**: Integration with calendar APIs
6. **Reference Checking**: Automated reference verification
7. **Skill Assessment**: Integration with coding challenge platforms

## Getting Help

When working with this codebase:

1. **Read the docs**: SETUP.md, AIRTABLE_SCHEMA.md, this file
2. **Check logs**: Detailed error messages in console output
3. **Test incrementally**: Start with single records
4. **Review examples**: Working patterns throughout the code
5. **Validate config**: Run `Config.validate()` first

## Version History

- **v1.0.0** (Current): Initial implementation with all core features
  - JSON compression/decompression
  - Rule-based shortlisting
  - Multi-provider LLM evaluation
  - Complete pipeline orchestration
