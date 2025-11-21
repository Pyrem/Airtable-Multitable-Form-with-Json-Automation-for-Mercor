"""
Configuration module for Airtable Multi-Table Form Automation
Loads settings from environment variables and provides validation.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Airtable Configuration
    AIRTABLE_API_KEY: str = os.getenv('AIRTABLE_API_KEY', '')
    AIRTABLE_BASE_ID: str = os.getenv('AIRTABLE_BASE_ID', '')

    # Table Names
    TABLE_APPLICANTS = 'Applicants'
    TABLE_PERSONAL_DETAILS = 'Personal Details'
    TABLE_WORK_EXPERIENCE = 'Work Experience'
    TABLE_SALARY_PREFERENCES = 'Salary Preferences'
    TABLE_SHORTLISTED_LEADS = 'Shortlisted Leads'

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'openai')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gpt-4')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    MAX_TOKENS_PER_CALL: int = int(os.getenv('MAX_TOKENS_PER_CALL', '1000'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))

    # Shortlist Criteria
    TIER_1_COMPANIES: List[str] = os.getenv(
        'TIER_1_COMPANIES',
        'Google,Meta,OpenAI,Microsoft,Amazon,Apple,Netflix,Anthropic'
    ).split(',')
    MAX_HOURLY_RATE: float = float(os.getenv('MAX_HOURLY_RATE', '100'))
    MIN_AVAILABILITY_HOURS: int = int(os.getenv('MIN_AVAILABILITY_HOURS', '20'))
    MIN_YEARS_EXPERIENCE: int = int(os.getenv('MIN_YEARS_EXPERIENCE', '4'))
    APPROVED_LOCATIONS: List[str] = os.getenv(
        'APPROVED_LOCATIONS',
        'US,USA,United States,Canada,UK,United Kingdom,Germany,India'
    ).split(',')

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        errors = []

        if not cls.AIRTABLE_API_KEY:
            errors.append("AIRTABLE_API_KEY is required")

        if not cls.AIRTABLE_BASE_ID:
            errors.append("AIRTABLE_BASE_ID is required")

        if cls.LLM_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        elif cls.LLM_PROVIDER == 'anthropic' and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        elif cls.LLM_PROVIDER == 'gemini' and not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required when using Gemini provider")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def get_llm_api_key(cls) -> str:
        """Get the appropriate API key based on the selected LLM provider."""
        if cls.LLM_PROVIDER == 'openai':
            return cls.OPENAI_API_KEY
        elif cls.LLM_PROVIDER == 'anthropic':
            return cls.ANTHROPIC_API_KEY
        elif cls.LLM_PROVIDER == 'gemini':
            return cls.GEMINI_API_KEY
        else:
            raise ValueError(f"Unknown LLM provider: {cls.LLM_PROVIDER}")
