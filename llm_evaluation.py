"""
LLM Evaluation & Enrichment Script
Uses LLM API (OpenAI, Anthropic, or Gemini) to evaluate applicants,
provide summaries, scores, and follow-up questions.
"""

import json
import logging
import time
import re
from typing import Dict, Any, Optional
from airtable_utils import AirtableClient
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMEvaluator:
    """Wrapper for LLM API calls with retry logic."""

    def __init__(self):
        """Initialize LLM client based on configured provider."""
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL
        self.max_tokens = Config.MAX_TOKENS_PER_CALL
        self.max_retries = Config.MAX_RETRIES

        if self.provider == 'openai':
            import openai
            self.client = openai.OpenAI(api_key=Config.get_llm_api_key())
        elif self.provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.get_llm_api_key())
        elif self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=Config.get_llm_api_key())
            self.client = genai.GenerativeModel(self.model)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a recruiting analyst evaluating candidate profiles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Google Gemini API."""
        try:
            response = self.client.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def call_llm(self, prompt: str) -> Optional[str]:
        """
        Call LLM API with retry logic.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            LLM response text or None on failure
        """
        for attempt in range(self.max_retries):
            try:
                if self.provider == 'openai':
                    response = self._call_openai(prompt)
                elif self.provider == 'anthropic':
                    response = self._call_anthropic(prompt)
                elif self.provider == 'gemini':
                    response = self._call_gemini(prompt)
                else:
                    return None

                if response:
                    return response

            except Exception as e:
                logger.error(f"LLM API call attempt {attempt + 1} failed: {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        logger.error(f"All {self.max_retries} LLM API call attempts failed")
        return None


def build_evaluation_prompt(compressed_json: str) -> str:
    """
    Build the LLM prompt for evaluating an applicant.

    Args:
        compressed_json: JSON string of applicant data

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a recruiting analyst. Given this JSON applicant profile, do four things:

1. Provide a concise 75-word summary of the candidate.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

Applicant Profile:
```json
{compressed_json}
```

Return your response in exactly this format:

Summary: <text>
Score: <integer>
Issues: <comma-separated list or 'None'>
Follow-Ups:
- <question 1>
- <question 2>
- <question 3>

If there are fewer than three follow-up questions, that's fine. Just list what's relevant.
"""
    return prompt


def parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse the structured response from the LLM.

    Args:
        response: Raw LLM response text

    Returns:
        Dictionary with parsed fields
    """
    result = {
        'summary': '',
        'score': 0,
        'issues': '',
        'follow_ups': ''
    }

    try:
        # Extract Summary
        summary_match = re.search(r'Summary:\s*(.+?)(?=\n(?:Score:|$))', response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()

        # Extract Score
        score_match = re.search(r'Score:\s*(\d+)', response, re.IGNORECASE)
        if score_match:
            result['score'] = int(score_match.group(1))

        # Extract Issues
        issues_match = re.search(r'Issues:\s*(.+?)(?=\n(?:Follow-Ups:|$))', response, re.DOTALL | re.IGNORECASE)
        if issues_match:
            result['issues'] = issues_match.group(1).strip()

        # Extract Follow-Ups
        followups_match = re.search(r'Follow-Ups:\s*(.+?)$', response, re.DOTALL | re.IGNORECASE)
        if followups_match:
            result['follow_ups'] = followups_match.group(1).strip()

    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")

    return result


def evaluate_applicant_with_llm(
    client: AirtableClient,
    llm_evaluator: LLMEvaluator,
    applicant_id: str,
    force: bool = False
) -> bool:
    """
    Evaluate an applicant using LLM and update their record.

    Args:
        client: AirtableClient instance
        llm_evaluator: LLMEvaluator instance
        applicant_id: The Airtable record ID of the applicant
        force: Force re-evaluation even if already evaluated

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Evaluating applicant {applicant_id} with LLM")

    try:
        # Get applicant record
        applicant = client.get_applicant(applicant_id)
        if not applicant:
            logger.error(f"Applicant {applicant_id} not found")
            return False

        fields = applicant.get('fields', {})
        compressed_json = fields.get('Compressed JSON')

        if not compressed_json:
            logger.warning(f"No Compressed JSON for applicant {applicant_id}")
            return False

        # Check if already evaluated (unless forced)
        if not force and fields.get('LLM Summary'):
            logger.info(f"Applicant {applicant_id} already evaluated. Use --force to re-evaluate.")
            return True

        # Build prompt
        prompt = build_evaluation_prompt(compressed_json)

        # Call LLM
        logger.info(f"Calling {llm_evaluator.provider} API...")
        response = llm_evaluator.call_llm(prompt)

        if not response:
            logger.error(f"Failed to get LLM response for applicant {applicant_id}")
            return False

        # Parse response
        parsed = parse_llm_response(response)

        # Update applicant record
        update_fields = {
            'LLM Summary': parsed['summary'],
            'LLM Score': parsed['score'],
            'LLM Issues': parsed['issues'],
            'LLM Follow-Ups': parsed['follow_ups']
        }

        result = client.update_applicant(applicant_id, update_fields)

        if result:
            logger.info(f"Successfully updated LLM evaluation for applicant {applicant_id}")
            logger.info(f"Score: {parsed['score']}/10")
            return True
        else:
            logger.error(f"Failed to update applicant {applicant_id}")
            return False

    except Exception as e:
        logger.error(f"Error evaluating applicant {applicant_id}: {e}")
        return False


def evaluate_all_applicants(
    client: AirtableClient,
    llm_evaluator: LLMEvaluator,
    force: bool = False
) -> None:
    """
    Evaluate all applicants with LLM.

    Args:
        client: AirtableClient instance
        llm_evaluator: LLMEvaluator instance
        force: Force re-evaluation of already evaluated applicants
    """
    logger.info("Starting LLM evaluation for all applicants")

    applicants = client.get_all_applicants()
    logger.info(f"Found {len(applicants)} applicants to process")

    success_count = 0
    skipped_count = 0
    failure_count = 0

    for applicant in applicants:
        applicant_id = applicant['id']
        fields = applicant.get('fields', {})

        # Skip if already evaluated (unless forced)
        if not force and fields.get('LLM Summary'):
            logger.info(f"Skipping already evaluated applicant {applicant_id}")
            skipped_count += 1
            continue

        if evaluate_applicant_with_llm(client, llm_evaluator, applicant_id, force):
            success_count += 1
        else:
            failure_count += 1

        # Small delay to avoid rate limiting
        time.sleep(1)

    logger.info(f"Evaluation complete: {success_count} successful, {skipped_count} skipped, {failure_count} failed")


def main():
    """Main entry point for the LLM evaluation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Evaluate applicants using LLM API'
    )
    parser.add_argument(
        '--applicant-id',
        type=str,
        help='Specific applicant ID to evaluate (optional)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Evaluate all applicants'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-evaluation even if already evaluated'
    )

    args = parser.parse_args()

    # Initialize clients
    client = AirtableClient()
    llm_evaluator = LLMEvaluator()

    if args.applicant_id:
        # Evaluate specific applicant
        success = evaluate_applicant_with_llm(client, llm_evaluator, args.applicant_id, args.force)
        if success:
            print(f"Successfully evaluated applicant {args.applicant_id}")
        else:
            print(f"Failed to evaluate applicant {args.applicant_id}")
    elif args.all:
        # Evaluate all applicants
        evaluate_all_applicants(client, llm_evaluator, args.force)
    else:
        print("Please specify either --applicant-id or --all")
        parser.print_help()


if __name__ == '__main__':
    main()
