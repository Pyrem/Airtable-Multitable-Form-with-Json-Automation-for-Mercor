"""
Utility functions for interacting with Airtable API.
Provides helper methods for reading and writing data across multiple tables.
"""

from typing import Dict, List, Any, Optional
from pyairtable import Api
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirtableClient:
    """Wrapper for Airtable API operations."""

    def __init__(self):
        """Initialize Airtable API client."""
        Config.validate()
        self.api = Api(Config.AIRTABLE_API_KEY)
        self.base = self.api.base(Config.AIRTABLE_BASE_ID)

        # Initialize table references
        self.applicants = self.base.table(Config.TABLE_APPLICANTS)
        self.personal_details = self.base.table(Config.TABLE_PERSONAL_DETAILS)
        self.work_experience = self.base.table(Config.TABLE_WORK_EXPERIENCE)
        self.salary_preferences = self.base.table(Config.TABLE_SALARY_PREFERENCES)
        self.shortlisted_leads = self.base.table(Config.TABLE_SHORTLISTED_LEADS)

    def get_applicant(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an applicant record by ID.

        Args:
            applicant_id: The Airtable record ID

        Returns:
            Dictionary containing applicant data or None if not found
        """
        try:
            record = self.applicants.get(applicant_id)
            return record
        except Exception as e:
            logger.error(f"Error retrieving applicant {applicant_id}: {e}")
            return None

    def get_all_applicants(self) -> List[Dict[str, Any]]:
        """
        Retrieve all applicant records.

        Returns:
            List of applicant records
        """
        try:
            records = self.applicants.all()
            return records
        except Exception as e:
            logger.error(f"Error retrieving all applicants: {e}")
            return []

    def get_personal_details(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve personal details linked to an applicant.

        Args:
            applicant_id: The Airtable record ID of the applicant

        Returns:
            Personal details record or None
        """
        try:
            formula = f"{{Applicant ID}} = '{applicant_id}'"
            records = self.personal_details.all(formula=formula)
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error retrieving personal details for {applicant_id}: {e}")
            return None

    def get_work_experiences(self, applicant_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all work experience records linked to an applicant.

        Args:
            applicant_id: The Airtable record ID of the applicant

        Returns:
            List of work experience records
        """
        try:
            formula = f"{{Applicant ID}} = '{applicant_id}'"
            records = self.work_experience.all(formula=formula)
            return records
        except Exception as e:
            logger.error(f"Error retrieving work experience for {applicant_id}: {e}")
            return []

    def get_salary_preferences(self, applicant_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve salary preferences linked to an applicant.

        Args:
            applicant_id: The Airtable record ID of the applicant

        Returns:
            Salary preferences record or None
        """
        try:
            formula = f"{{Applicant ID}} = '{applicant_id}'"
            records = self.salary_preferences.all(formula=formula)
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error retrieving salary preferences for {applicant_id}: {e}")
            return None

    def update_applicant(self, applicant_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an applicant record.

        Args:
            applicant_id: The Airtable record ID
            fields: Dictionary of fields to update

        Returns:
            Updated record or None on failure
        """
        try:
            record = self.applicants.update(applicant_id, fields)
            logger.info(f"Updated applicant {applicant_id}")
            return record
        except Exception as e:
            logger.error(f"Error updating applicant {applicant_id}: {e}")
            return None

    def create_personal_details(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a personal details record."""
        try:
            record = self.personal_details.create(fields)
            logger.info(f"Created personal details record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error creating personal details: {e}")
            return None

    def update_personal_details(self, record_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a personal details record."""
        try:
            record = self.personal_details.update(record_id, fields)
            logger.info(f"Updated personal details {record_id}")
            return record
        except Exception as e:
            logger.error(f"Error updating personal details {record_id}: {e}")
            return None

    def create_work_experience(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a work experience record."""
        try:
            record = self.work_experience.create(fields)
            logger.info(f"Created work experience record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error creating work experience: {e}")
            return None

    def update_work_experience(self, record_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a work experience record."""
        try:
            record = self.work_experience.update(record_id, fields)
            logger.info(f"Updated work experience {record_id}")
            return record
        except Exception as e:
            logger.error(f"Error updating work experience {record_id}: {e}")
            return None

    def delete_work_experience(self, record_id: str) -> bool:
        """Delete a work experience record."""
        try:
            self.work_experience.delete(record_id)
            logger.info(f"Deleted work experience {record_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting work experience {record_id}: {e}")
            return False

    def create_salary_preferences(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a salary preferences record."""
        try:
            record = self.salary_preferences.create(fields)
            logger.info(f"Created salary preferences record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error creating salary preferences: {e}")
            return None

    def update_salary_preferences(self, record_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a salary preferences record."""
        try:
            record = self.salary_preferences.update(record_id, fields)
            logger.info(f"Updated salary preferences {record_id}")
            return record
        except Exception as e:
            logger.error(f"Error updating salary preferences {record_id}: {e}")
            return None

    def create_shortlisted_lead(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a shortlisted lead record."""
        try:
            record = self.shortlisted_leads.create(fields)
            logger.info(f"Created shortlisted lead record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error creating shortlisted lead: {e}")
            return None

    def check_shortlisted_lead_exists(self, applicant_id: str) -> bool:
        """
        Check if a shortlisted lead already exists for an applicant.

        Args:
            applicant_id: The Airtable record ID of the applicant

        Returns:
            True if a shortlisted lead exists, False otherwise
        """
        try:
            formula = f"{{Applicant}} = '{applicant_id}'"
            records = self.shortlisted_leads.all(formula=formula)
            return len(records) > 0
        except Exception as e:
            logger.error(f"Error checking shortlisted lead for {applicant_id}: {e}")
            return False
