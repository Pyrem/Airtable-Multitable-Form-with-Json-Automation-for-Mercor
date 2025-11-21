"""
JSON Compression Script
Gathers data from three linked tables (Personal Details, Work Experience, Salary Preferences)
and compresses it into a single JSON object stored in the Applicants table.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from airtable_utils import AirtableClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_total_experience(work_experiences: list) -> float:
    """
    Calculate total years of experience from work experience records.

    Args:
        work_experiences: List of work experience records

    Returns:
        Total years of experience
    """
    total_years = 0.0

    for exp in work_experiences:
        fields = exp.get('fields', {})
        start_date = fields.get('Start Date')
        end_date = fields.get('End Date')

        if not start_date:
            continue

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                # If no end date, assume current
                end = datetime.now()

            years = (end - start).days / 365.25
            total_years += years
        except Exception as e:
            logger.warning(f"Error calculating experience duration: {e}")
            continue

    return round(total_years, 1)


def compress_applicant_data(client: AirtableClient, applicant_id: str) -> Optional[Dict[str, Any]]:
    """
    Compress data from multiple tables into a single JSON object.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant

    Returns:
        Compressed JSON data or None on failure
    """
    logger.info(f"Compressing data for applicant: {applicant_id}")

    # Fetch data from all linked tables
    personal = client.get_personal_details(applicant_id)
    experiences = client.get_work_experiences(applicant_id)
    salary = client.get_salary_preferences(applicant_id)

    # Build compressed JSON structure
    compressed_data = {}

    # Personal Details
    if personal:
        personal_fields = personal.get('fields', {})
        compressed_data['personal'] = {
            'name': personal_fields.get('Full Name', ''),
            'email': personal_fields.get('Email', ''),
            'location': personal_fields.get('Location', ''),
            'linkedin': personal_fields.get('LinkedIn', '')
        }
    else:
        logger.warning(f"No personal details found for applicant {applicant_id}")
        compressed_data['personal'] = {}

    # Work Experience
    if experiences:
        compressed_data['experience'] = []
        for exp in experiences:
            exp_fields = exp.get('fields', {})
            compressed_data['experience'].append({
                'company': exp_fields.get('Company', ''),
                'title': exp_fields.get('Title', ''),
                'start_date': exp_fields.get('Start Date', ''),
                'end_date': exp_fields.get('End Date', ''),
                'technologies': exp_fields.get('Technologies', ''),
                'description': exp_fields.get('Description', '')
            })

        # Calculate total experience
        total_exp = calculate_total_experience(experiences)
        compressed_data['total_experience_years'] = total_exp
    else:
        logger.warning(f"No work experience found for applicant {applicant_id}")
        compressed_data['experience'] = []
        compressed_data['total_experience_years'] = 0

    # Salary Preferences
    if salary:
        salary_fields = salary.get('fields', {})
        compressed_data['salary'] = {
            'preferred_rate': salary_fields.get('Preferred Rate', 0),
            'minimum_rate': salary_fields.get('Minimum Rate', 0),
            'currency': salary_fields.get('Currency', 'USD'),
            'availability': salary_fields.get('Availability (hrs/wk)', 0)
        }
    else:
        logger.warning(f"No salary preferences found for applicant {applicant_id}")
        compressed_data['salary'] = {}

    return compressed_data


def update_compressed_json(client: AirtableClient, applicant_id: str) -> bool:
    """
    Compress applicant data and update the Compressed JSON field.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant

    Returns:
        True if successful, False otherwise
    """
    try:
        # Compress the data
        compressed_data = compress_applicant_data(client, applicant_id)

        if not compressed_data:
            logger.error(f"Failed to compress data for applicant {applicant_id}")
            return False

        # Convert to JSON string
        json_string = json.dumps(compressed_data, indent=2)

        # Update the Applicants table
        result = client.update_applicant(applicant_id, {
            'Compressed JSON': json_string
        })

        if result:
            logger.info(f"Successfully updated Compressed JSON for applicant {applicant_id}")
            return True
        else:
            logger.error(f"Failed to update Compressed JSON for applicant {applicant_id}")
            return False

    except Exception as e:
        logger.error(f"Error updating compressed JSON for {applicant_id}: {e}")
        return False


def compress_all_applicants(client: AirtableClient) -> None:
    """
    Compress data for all applicants in the database.

    Args:
        client: AirtableClient instance
    """
    logger.info("Starting compression for all applicants")

    applicants = client.get_all_applicants()
    logger.info(f"Found {len(applicants)} applicants to process")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        applicant_id = applicant['id']
        if update_compressed_json(client, applicant_id):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Compression complete: {success_count} successful, {failure_count} failed")


def main():
    """Main entry point for the compression script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Compress applicant data from multiple tables into JSON'
    )
    parser.add_argument(
        '--applicant-id',
        type=str,
        help='Specific applicant ID to compress (optional)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Compress data for all applicants'
    )

    args = parser.parse_args()

    # Initialize Airtable client
    client = AirtableClient()

    if args.applicant_id:
        # Compress specific applicant
        success = update_compressed_json(client, args.applicant_id)
        if success:
            print(f"Successfully compressed data for applicant {args.applicant_id}")
        else:
            print(f"Failed to compress data for applicant {args.applicant_id}")
    elif args.all:
        # Compress all applicants
        compress_all_applicants(client)
    else:
        print("Please specify either --applicant-id or --all")
        parser.print_help()


if __name__ == '__main__':
    main()
