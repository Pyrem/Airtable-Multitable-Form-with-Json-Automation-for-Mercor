"""
JSON Decompression Script
Reads the Compressed JSON field from the Applicants table and upserts
child-table records to match the JSON state exactly.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from airtable_utils import AirtableClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def upsert_personal_details(
    client: AirtableClient,
    applicant_id: str,
    personal_data: Dict[str, Any]
) -> bool:
    """
    Upsert personal details record.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant
        personal_data: Personal details from JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if record exists
        existing = client.get_personal_details(applicant_id)

        fields = {
            'Applicant ID': [applicant_id],
            'Full Name': personal_data.get('name', ''),
            'Email': personal_data.get('email', ''),
            'Location': personal_data.get('location', ''),
            'LinkedIn': personal_data.get('linkedin', '')
        }

        if existing:
            # Update existing record
            result = client.update_personal_details(existing['id'], fields)
        else:
            # Create new record
            result = client.create_personal_details(fields)

        return result is not None

    except Exception as e:
        logger.error(f"Error upserting personal details: {e}")
        return False


def upsert_work_experiences(
    client: AirtableClient,
    applicant_id: str,
    experience_data: List[Dict[str, Any]]
) -> bool:
    """
    Upsert work experience records to match JSON state.
    Deletes records that are no longer in the JSON.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant
        experience_data: List of work experiences from JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get existing work experience records
        existing_records = client.get_work_experiences(applicant_id)

        # Track which records we've processed
        processed_ids = set()

        # Upsert each experience from JSON
        for idx, exp in enumerate(experience_data):
            fields = {
                'Applicant ID': [applicant_id],
                'Company': exp.get('company', ''),
                'Title': exp.get('title', ''),
                'Start Date': exp.get('start_date', ''),
                'End Date': exp.get('end_date', ''),
                'Technologies': exp.get('technologies', ''),
                'Description': exp.get('description', '')
            }

            # Try to match with existing record (by index or company name)
            if idx < len(existing_records):
                record_id = existing_records[idx]['id']
                client.update_work_experience(record_id, fields)
                processed_ids.add(record_id)
            else:
                # Create new record
                new_record = client.create_work_experience(fields)
                if new_record:
                    processed_ids.add(new_record['id'])

        # Delete any existing records that weren't in the JSON
        for existing in existing_records:
            if existing['id'] not in processed_ids:
                client.delete_work_experience(existing['id'])

        return True

    except Exception as e:
        logger.error(f"Error upserting work experiences: {e}")
        return False


def upsert_salary_preferences(
    client: AirtableClient,
    applicant_id: str,
    salary_data: Dict[str, Any]
) -> bool:
    """
    Upsert salary preferences record.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant
        salary_data: Salary preferences from JSON

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if record exists
        existing = client.get_salary_preferences(applicant_id)

        fields = {
            'Applicant ID': [applicant_id],
            'Preferred Rate': salary_data.get('preferred_rate', 0),
            'Minimum Rate': salary_data.get('minimum_rate', 0),
            'Currency': salary_data.get('currency', 'USD'),
            'Availability (hrs/wk)': salary_data.get('availability', 0)
        }

        if existing:
            # Update existing record
            result = client.update_salary_preferences(existing['id'], fields)
        else:
            # Create new record
            result = client.create_salary_preferences(fields)

        return result is not None

    except Exception as e:
        logger.error(f"Error upserting salary preferences: {e}")
        return False


def decompress_applicant_data(client: AirtableClient, applicant_id: str) -> bool:
    """
    Read Compressed JSON and update all child tables to match.

    Args:
        client: AirtableClient instance
        applicant_id: The Airtable record ID of the applicant

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Decompressing data for applicant: {applicant_id}")

    try:
        # Get the applicant record
        applicant = client.get_applicant(applicant_id)

        if not applicant:
            logger.error(f"Applicant {applicant_id} not found")
            return False

        # Get the Compressed JSON field
        compressed_json = applicant.get('fields', {}).get('Compressed JSON')

        if not compressed_json:
            logger.error(f"No Compressed JSON found for applicant {applicant_id}")
            return False

        # Parse JSON
        try:
            data = json.loads(compressed_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON for applicant {applicant_id}: {e}")
            return False

        # Upsert data to child tables
        success = True

        # Personal Details
        if 'personal' in data:
            if not upsert_personal_details(client, applicant_id, data['personal']):
                success = False
                logger.error("Failed to upsert personal details")

        # Work Experience
        if 'experience' in data:
            if not upsert_work_experiences(client, applicant_id, data['experience']):
                success = False
                logger.error("Failed to upsert work experiences")

        # Salary Preferences
        if 'salary' in data:
            if not upsert_salary_preferences(client, applicant_id, data['salary']):
                success = False
                logger.error("Failed to upsert salary preferences")

        if success:
            logger.info(f"Successfully decompressed data for applicant {applicant_id}")
        else:
            logger.warning(f"Partially decompressed data for applicant {applicant_id}")

        return success

    except Exception as e:
        logger.error(f"Error decompressing data for {applicant_id}: {e}")
        return False


def decompress_all_applicants(client: AirtableClient) -> None:
    """
    Decompress data for all applicants in the database.

    Args:
        client: AirtableClient instance
    """
    logger.info("Starting decompression for all applicants")

    applicants = client.get_all_applicants()
    logger.info(f"Found {len(applicants)} applicants to process")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        applicant_id = applicant['id']
        if decompress_applicant_data(client, applicant_id):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Decompression complete: {success_count} successful, {failure_count} failed")


def main():
    """Main entry point for the decompression script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Decompress JSON back to normalized Airtable tables'
    )
    parser.add_argument(
        '--applicant-id',
        type=str,
        help='Specific applicant ID to decompress (optional)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Decompress data for all applicants'
    )

    args = parser.parse_args()

    # Initialize Airtable client
    client = AirtableClient()

    if args.applicant_id:
        # Decompress specific applicant
        success = decompress_applicant_data(client, args.applicant_id)
        if success:
            print(f"Successfully decompressed data for applicant {args.applicant_id}")
        else:
            print(f"Failed to decompress data for applicant {args.applicant_id}")
    elif args.all:
        # Decompress all applicants
        decompress_all_applicants(client)
    else:
        print("Please specify either --applicant-id or --all")
        parser.print_help()


if __name__ == '__main__':
    main()
