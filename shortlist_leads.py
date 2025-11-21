"""
Lead Shortlist Automation Script
Evaluates applicants against defined criteria and creates Shortlisted Leads records
for candidates that meet all requirements.

Criteria:
1. Experience: >= 4 years total OR worked at a Tier-1 company
2. Compensation: Preferred Rate <= $100 USD/hour AND Availability >= 20 hrs/week
3. Location: In approved countries (US, Canada, UK, Germany, India)
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from airtable_utils import AirtableClient
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def normalize_location(location: str) -> str:
    """Normalize location string for comparison."""
    if not location:
        return ""
    return location.strip().lower()


def check_location_criteria(location: str) -> bool:
    """
    Check if applicant's location meets criteria.

    Args:
        location: Location string from applicant data

    Returns:
        True if location is approved, False otherwise
    """
    if not location:
        return False

    normalized_location = normalize_location(location)

    # Check against approved locations
    for approved in Config.APPROVED_LOCATIONS:
        if normalize_location(approved) in normalized_location:
            return True

    return False


def check_experience_criteria(compressed_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if applicant meets experience criteria.

    Args:
        compressed_data: Parsed JSON data from Compressed JSON field

    Returns:
        Tuple of (meets_criteria, reason)
    """
    # Check total years of experience
    total_years = compressed_data.get('total_experience_years', 0)
    if total_years >= Config.MIN_YEARS_EXPERIENCE:
        return True, f"Has {total_years} years of experience (>= {Config.MIN_YEARS_EXPERIENCE} required)"

    # Check if worked at Tier-1 company
    experiences = compressed_data.get('experience', [])
    tier1_companies = []

    for exp in experiences:
        company = exp.get('company', '').strip()
        for tier1 in Config.TIER_1_COMPANIES:
            if tier1.strip().lower() in company.lower():
                tier1_companies.append(company)
                break

    if tier1_companies:
        return True, f"Worked at Tier-1 company: {', '.join(set(tier1_companies))}"

    return False, f"Only {total_years} years experience and no Tier-1 company experience"


def check_compensation_criteria(compressed_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if applicant meets compensation criteria.

    Args:
        compressed_data: Parsed JSON data from Compressed JSON field

    Returns:
        Tuple of (meets_criteria, reason)
    """
    salary = compressed_data.get('salary', {})
    preferred_rate = salary.get('preferred_rate', float('inf'))
    availability = salary.get('availability', 0)
    currency = salary.get('currency', 'USD').upper()

    # For simplicity, assume all rates are in USD or convert if needed
    # In production, you'd want proper currency conversion
    if currency != 'USD':
        logger.warning(f"Non-USD currency detected: {currency}. Treating as USD for comparison.")

    reasons = []

    # Check rate
    if preferred_rate > Config.MAX_HOURLY_RATE:
        reasons.append(f"Rate ${preferred_rate}/hr exceeds max ${Config.MAX_HOURLY_RATE}/hr")

    # Check availability
    if availability < Config.MIN_AVAILABILITY_HOURS:
        reasons.append(f"Availability {availability} hrs/wk below min {Config.MIN_AVAILABILITY_HOURS} hrs/wk")

    if reasons:
        return False, "; ".join(reasons)

    return True, f"Rate ${preferred_rate}/hr <= ${Config.MAX_HOURLY_RATE}/hr and {availability} hrs/wk >= {Config.MIN_AVAILABILITY_HOURS} hrs/wk"


def evaluate_applicant(client: AirtableClient, applicant_id: str) -> Optional[Dict[str, Any]]:
    """
    Evaluate an applicant against shortlist criteria.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant

    Returns:
        Dictionary with evaluation results or None on error
    """
    logger.info(f"Evaluating applicant: {applicant_id}")

    try:
        # Get applicant record
        applicant = client.get_applicant(applicant_id)
        if not applicant:
            logger.error(f"Applicant {applicant_id} not found")
            return None

        # Get compressed JSON
        compressed_json = applicant.get('fields', {}).get('Compressed JSON')
        if not compressed_json:
            logger.warning(f"No Compressed JSON for applicant {applicant_id}")
            return None

        # Parse JSON
        try:
            data = json.loads(compressed_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON for applicant {applicant_id}: {e}")
            return None

        # Evaluate each criterion
        criteria_results = {}

        # 1. Location
        location = data.get('personal', {}).get('location', '')
        location_ok = check_location_criteria(location)
        criteria_results['location'] = {
            'passed': location_ok,
            'reason': f"Location '{location}' is {'approved' if location_ok else 'not approved'}"
        }

        # 2. Experience
        exp_ok, exp_reason = check_experience_criteria(data)
        criteria_results['experience'] = {
            'passed': exp_ok,
            'reason': exp_reason
        }

        # 3. Compensation
        comp_ok, comp_reason = check_compensation_criteria(data)
        criteria_results['compensation'] = {
            'passed': comp_ok,
            'reason': comp_reason
        }

        # Overall result
        all_passed = all(c['passed'] for c in criteria_results.values())

        return {
            'applicant_id': applicant_id,
            'shortlisted': all_passed,
            'criteria': criteria_results,
            'compressed_json': compressed_json
        }

    except Exception as e:
        logger.error(f"Error evaluating applicant {applicant_id}: {e}")
        return None


def create_shortlisted_lead(client: AirtableClient, evaluation: Dict[str, Any]) -> bool:
    """
    Create a Shortlisted Leads record if criteria are met.

    Args:
        client: AirtableClient instance
        evaluation: Evaluation results from evaluate_applicant

    Returns:
        True if lead created or already exists, False otherwise
    """
    if not evaluation['shortlisted']:
        logger.info(f"Applicant {evaluation['applicant_id']} does not meet criteria")
        return False

    applicant_id = evaluation['applicant_id']

    # Check if already shortlisted
    if client.check_shortlisted_lead_exists(applicant_id):
        logger.info(f"Applicant {applicant_id} already shortlisted")
        return True

    # Build score reason
    reasons = []
    for criterion, result in evaluation['criteria'].items():
        reasons.append(f"{criterion.title()}: {result['reason']}")

    score_reason = "\n".join(reasons)

    # Create shortlisted lead record
    fields = {
        'Applicant': [applicant_id],
        'Compressed JSON': evaluation['compressed_json'],
        'Score Reason': score_reason,
        'Created At': datetime.now().isoformat()
    }

    result = client.create_shortlisted_lead(fields)

    if result:
        logger.info(f"Created shortlisted lead for applicant {applicant_id}")
        # Update applicant's shortlist status
        client.update_applicant(applicant_id, {'Shortlist Status': 'Shortlisted'})
        return True
    else:
        logger.error(f"Failed to create shortlisted lead for applicant {applicant_id}")
        return False


def process_applicant(client: AirtableClient, applicant_id: str) -> bool:
    """
    Evaluate and potentially shortlist an applicant.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant

    Returns:
        True if processed successfully, False otherwise
    """
    evaluation = evaluate_applicant(client, applicant_id)

    if not evaluation:
        return False

    if evaluation['shortlisted']:
        return create_shortlisted_lead(client, evaluation)
    else:
        # Update status to not shortlisted
        client.update_applicant(applicant_id, {'Shortlist Status': 'Not Shortlisted'})
        logger.info(f"Applicant {applicant_id} not shortlisted")
        return True


def process_all_applicants(client: AirtableClient) -> None:
    """
    Process all applicants for shortlisting.

    Args:
        client: AirtableClient instance
    """
    logger.info("Processing all applicants for shortlisting")

    applicants = client.get_all_applicants()
    logger.info(f"Found {len(applicants)} applicants to process")

    shortlisted_count = 0
    processed_count = 0

    for applicant in applicants:
        applicant_id = applicant['id']
        if process_applicant(client, applicant_id):
            processed_count += 1
            # Check if shortlisted
            if client.check_shortlisted_lead_exists(applicant_id):
                shortlisted_count += 1

    logger.info(f"Processing complete: {processed_count} processed, {shortlisted_count} shortlisted")


def main():
    """Main entry point for the shortlist automation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Evaluate and shortlist applicants based on criteria'
    )
    parser.add_argument(
        '--applicant-id',
        type=str,
        help='Specific applicant ID to process (optional)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all applicants'
    )

    args = parser.parse_args()

    # Initialize Airtable client
    client = AirtableClient()

    if args.applicant_id:
        # Process specific applicant
        success = process_applicant(client, args.applicant_id)
        if success:
            print(f"Successfully processed applicant {args.applicant_id}")
        else:
            print(f"Failed to process applicant {args.applicant_id}")
    elif args.all:
        # Process all applicants
        process_all_applicants(client)
    else:
        print("Please specify either --applicant-id or --all")
        parser.print_help()


if __name__ == '__main__':
    main()
