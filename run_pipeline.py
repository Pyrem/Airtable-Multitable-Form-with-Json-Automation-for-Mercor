"""
Master Pipeline Script
Orchestrates the complete workflow:
1. Compress applicant data to JSON
2. Evaluate and shortlist candidates
3. Run LLM evaluation and enrichment
"""

import logging
import argparse
from airtable_utils import AirtableClient
from compress_json import update_compressed_json, compress_all_applicants
from shortlist_leads import process_applicant as shortlist_applicant, process_all_applicants as shortlist_all
from llm_evaluation import LLMEvaluator, evaluate_applicant_with_llm, evaluate_all_applicants

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline_for_applicant(applicant_id: str, force_llm: bool = False) -> bool:
    """
    Run the complete pipeline for a single applicant.

    Args:
        applicant_id: The Airtable record ID of the applicant
        force_llm: Force LLM re-evaluation even if already evaluated

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Running pipeline for applicant {applicant_id}")

    try:
        # Initialize clients
        client = AirtableClient()
        llm_evaluator = LLMEvaluator()

        # Step 1: Compress data to JSON
        logger.info("Step 1: Compressing data to JSON...")
        if not update_compressed_json(client, applicant_id):
            logger.error("Failed to compress data")
            return False

        # Step 2: Evaluate for shortlisting
        logger.info("Step 2: Evaluating for shortlisting...")
        if not shortlist_applicant(client, applicant_id):
            logger.error("Failed to shortlist evaluation")
            return False

        # Step 3: LLM evaluation
        logger.info("Step 3: Running LLM evaluation...")
        if not evaluate_applicant_with_llm(client, llm_evaluator, applicant_id, force_llm):
            logger.error("Failed LLM evaluation")
            return False

        logger.info(f"Pipeline completed successfully for applicant {applicant_id}")
        return True

    except Exception as e:
        logger.error(f"Pipeline error for applicant {applicant_id}: {e}")
        return False


def run_pipeline_for_all(force_llm: bool = False) -> None:
    """
    Run the complete pipeline for all applicants.

    Args:
        force_llm: Force LLM re-evaluation even if already evaluated
    """
    logger.info("Running pipeline for all applicants")

    try:
        # Initialize clients
        client = AirtableClient()
        llm_evaluator = LLMEvaluator()

        # Step 1: Compress all applicants
        logger.info("Step 1: Compressing data for all applicants...")
        compress_all_applicants(client)

        # Step 2: Shortlist evaluation for all
        logger.info("Step 2: Evaluating all applicants for shortlisting...")
        shortlist_all(client)

        # Step 3: LLM evaluation for all
        logger.info("Step 3: Running LLM evaluation for all applicants...")
        evaluate_all_applicants(client, llm_evaluator, force_llm)

        logger.info("Pipeline completed successfully for all applicants")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")


def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(
        description='Run the complete applicant processing pipeline'
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
    parser.add_argument(
        '--force-llm',
        action='store_true',
        help='Force LLM re-evaluation even if already evaluated'
    )

    args = parser.parse_args()

    if args.applicant_id:
        # Run pipeline for specific applicant
        success = run_pipeline_for_applicant(args.applicant_id, args.force_llm)
        if success:
            print(f"\nPipeline completed successfully for applicant {args.applicant_id}")
        else:
            print(f"\nPipeline failed for applicant {args.applicant_id}")
    elif args.all:
        # Run pipeline for all applicants
        run_pipeline_for_all(args.force_llm)
        print("\nPipeline completed for all applicants")
    else:
        print("Please specify either --applicant-id or --all")
        parser.print_help()


if __name__ == '__main__':
    main()
