# Airtable Multi-Table Form + JSON Automation

A comprehensive system for collecting, processing, and evaluating contractor applications using Airtable, Python automation, and LLM-powered analysis.

## Overview

This project implements an automated applicant management system that:

1. Collects contractor application data through structured, multi-table Airtable forms
2. Compresses data from multiple linked tables into a single JSON object for efficient storage
3. Decompresses JSON back to normalized tables when edits are needed
4. Auto-shortlists promising candidates based on configurable, multi-factor rules
5. Uses LLM APIs (OpenAI, Anthropic, or Gemini) to evaluate, enrich, and sanity-check applications

## Features

- **Multi-Table Data Management**: Normalized database schema with linked tables for personal details, work experience, and salary preferences
- **JSON Compression/Decompression**: Bidirectional transformation between normalized tables and compressed JSON
- **Automated Shortlisting**: Rule-based evaluation against experience, compensation, and location criteria
- **LLM-Powered Evaluation**: AI-generated summaries, quality scores, issue detection, and follow-up questions
- **Multiple LLM Provider Support**: Works with OpenAI, Anthropic Claude, and Google Gemini
- **Configurable Criteria**: Easy customization of shortlist rules via environment variables
- **Pipeline Orchestration**: Master script to run the complete workflow end-to-end
- **Robust Error Handling**: Retry logic with exponential backoff for API calls

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Airtable account with API access
- API key for at least one LLM provider (OpenAI, Anthropic, or Google Gemini)

### Installation

```bash
# Clone or download the repository
cd Airtable-Multitable-Form-with-Json-Automation-for-Mercor

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and base ID
```

### Configuration

Edit `.env` file with your credentials:

```bash
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id

# Choose one LLM provider
LLM_PROVIDER=openai  # or anthropic, gemini
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
```

### Usage

Run the complete pipeline for all applicants:

```bash
python run_pipeline.py --all
```

Or process a specific applicant:

```bash
python run_pipeline.py --applicant-id rec1234567890
```

## Documentation

- **[SETUP.md](SETUP.md)**: Complete setup and usage instructions
- **[AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md)**: Detailed Airtable schema documentation
- **[CLAUDE.md](CLAUDE.md)**: Comprehensive guide for AI assistants and developers

## Project Structure

```
.
├── config.py                   # Configuration management
├── airtable_utils.py           # Airtable API wrapper
├── compress_json.py            # Multi-table to JSON compression
├── decompress_json.py          # JSON to multi-table decompression
├── shortlist_leads.py          # Rule-based lead shortlisting
├── llm_evaluation.py           # LLM-based evaluation
├── run_pipeline.py             # Master orchestrator script
├── requirements.txt            # Python dependencies
└── .env.example                # Environment configuration template
```

## Shortlist Criteria

Applicants are automatically shortlisted if they meet ALL of the following criteria:

### 1. Experience
- 4+ years of total experience OR
- Worked at a Tier-1 company (Google, Meta, OpenAI, Microsoft, Amazon, Apple, Netflix, Anthropic)

### 2. Compensation
- Preferred hourly rate ≤ $100 USD AND
- Availability ≥ 20 hours per week

### 3. Location
- Located in: US, Canada, UK, Germany, or India

All criteria are configurable via environment variables.

## LLM Evaluation

The system uses LLM APIs to provide:

- **75-word summary** of the candidate
- **Quality score** from 1-10
- **Data gap detection** identifying missing or inconsistent information
- **Follow-up questions** (up to 3) to clarify gaps

### Supported LLM Providers

- **OpenAI**: GPT-4, GPT-3.5-Turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus
- **Google**: Gemini Pro

## Scripts

### Individual Components

Each component can be run independently:

```bash
# JSON Compression
python compress_json.py --all
python compress_json.py --applicant-id rec123

# JSON Decompression
python decompress_json.py --all
python decompress_json.py --applicant-id rec123

# Lead Shortlisting
python shortlist_leads.py --all
python shortlist_leads.py --applicant-id rec123

# LLM Evaluation
python llm_evaluation.py --all
python llm_evaluation.py --applicant-id rec123 --force
```

## Airtable Schema

The system uses 5 tables:

1. **Applicants** (parent): Stores applicant records with compressed JSON and LLM outputs
2. **Personal Details**: One-to-one with applicants (name, email, location, LinkedIn)
3. **Work Experience**: One-to-many with applicants (company, title, dates, technologies)
4. **Salary Preferences**: One-to-one with applicants (rates, currency, availability)
5. **Shortlisted Leads**: Auto-populated when criteria are met

See [AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md) for complete schema details and setup instructions.

## Workflow

### For New Applicants

1. Applicant submits three Airtable forms (Personal Details, Work Experience, Salary Preferences)
2. Run compression: `python compress_json.py --applicant-id rec123`
3. Run shortlist evaluation: `python shortlist_leads.py --applicant-id rec123`
4. Run LLM evaluation: `python llm_evaluation.py --applicant-id rec123`

Or simply: `python run_pipeline.py --applicant-id rec123`

### For Editing Applicant Data

1. Edit the Compressed JSON directly in Airtable, OR
2. Decompress: `python decompress_json.py --applicant-id rec123`
3. Edit individual table records in Airtable
4. Re-compress: `python compress_json.py --applicant-id rec123`
5. Re-run pipeline: `python run_pipeline.py --applicant-id rec123 --force-llm`

## Customization

### Modifying Shortlist Criteria

Edit `.env` file:

```bash
MAX_HOURLY_RATE=120
MIN_AVAILABILITY_HOURS=25
MIN_YEARS_EXPERIENCE=5
TIER_1_COMPANIES=Google,Meta,OpenAI,Microsoft,Amazon,Stripe,DeepMind
APPROVED_LOCATIONS=US,Canada,UK,Germany,India,Australia
```

### Customizing LLM Prompts

Edit `build_evaluation_prompt()` function in `llm_evaluation.py` to change evaluation criteria.

### Adding New Fields

1. Add field to appropriate Airtable table
2. Update `compress_json.py` to include field in JSON
3. Update `decompress_json.py` to handle field when decompressing
4. Update `airtable_utils.py` if new table is added

## Security

- Never commit `.env` file to version control
- Store API keys securely
- Use minimal required Airtable API scopes
- Monitor LLM API usage and costs
- Rotate API keys periodically

## Error Handling

All scripts include:

- Comprehensive error logging
- Try-except blocks around API calls
- Retry logic with exponential backoff for LLM calls
- Graceful failure handling

## Performance

- Built-in rate limiting protection
- Exponential backoff for retries
- Batch processing support
- Token usage controls for LLM calls

## Requirements

See `requirements.txt`:

- pyairtable==2.3.3
- python-dotenv==1.0.0
- openai==1.12.0
- anthropic==0.18.1
- google-generativeai==0.3.2
- requests==2.31.0

## Troubleshooting

### Common Issues

**Configuration errors**: Ensure `.env` file is created and contains all required keys

**Airtable API errors**: Verify API key, base ID, and table names match exactly

**LLM API failures**: Check API key validity, billing status, and rate limits

**Import errors**: Activate virtual environment and run `pip install -r requirements.txt`

See [SETUP.md](SETUP.md) for detailed troubleshooting guide.

## Development

For developers and AI assistants working with this codebase, see [CLAUDE.md](CLAUDE.md) for:

- Detailed architecture documentation
- Code conventions and patterns
- Development workflows
- Extension guidelines

## License

This project is created for the Mercor Mini-Interview Task.

## Support

For issues or questions:

1. Check documentation: SETUP.md, AIRTABLE_SCHEMA.md, CLAUDE.md
2. Review logs for error messages
3. Test with a single applicant before batch processing
4. Verify Airtable schema matches documentation

## Contributing

When contributing:

1. Follow existing code patterns and conventions
2. Update documentation for any changes
3. Test with sample data before processing real applicants
4. Keep security best practices in mind
