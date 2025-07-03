#!/usr/bin/env python3
"""
Bulk test data generator script for integration testing.
"""

import argparse
import json
import logging
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tests.conftest import TestConfig, TestUser, ValidationRule
from scripts.test_data_factory import TestDataFactory
from scripts.webhook_validator import WebhookValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> TestConfig:
    """Load test configuration from YAML file."""
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Parse test users
    test_users = []
    for user_data in config_data["test_users"]:
        test_users.append(TestUser(**user_data))
    
    # Parse validation rules
    validation_rules = []
    for rule_data in config_data.get("validation_rules", []):
        validation_rules.append(ValidationRule(**rule_data))
    
    return TestConfig(
        test_name=config_data["test_name"],
        webhook_url=config_data["webhook_url"],
        superuser_api_key=config_data["superuser_api_key"],
        integration_type=config_data["integration_type"],
        test_records=config_data["test_records"],
        distribution=config_data["distribution"],
        processing_delay=config_data["processing_delay"],
        test_users=test_users,
        validation_rules=validation_rules
    )


def load_payload_template(integration_type: str) -> Dict[str, Any]:
    """Load payload template for integration."""
    template_path = f"tests/fixtures/{integration_type}_payload_template.json"
    
    if not Path(template_path).exists():
        raise FileNotFoundError(f"Payload template not found: {template_path}")
    
    with open(template_path, 'r') as f:
        return json.load(f)


def generate_test_data(config: TestConfig, payload_template: Dict[str, Any], dry_run: bool = False) -> None:
    """Generate test data and optionally send to webhook."""
    # Generate test run ID
    test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"Starting test data generation for {config.integration_type}")
    logger.info(f"Test run ID: {test_run_id}")
    logger.info(f"Configuration: {config.test_records} records for {len(config.test_users)} users")
    
    # Create test data factory
    factory = TestDataFactory(config, payload_template)
    
    # Generate test records
    logger.info("Generating test records...")
    test_records = factory.generate_test_records(test_run_id)
    
    # Validate test records
    logger.info("Validating test records...")
    validation_results = factory.validate_test_records(test_records)
    
    if validation_results['validation_errors']:
        logger.error(f"Test data validation failed:")
        for error in validation_results['validation_errors']:
            logger.error(f"  - {error}")
        return
    
    logger.info("Test data validation passed")
    logger.info(f"Generated {validation_results['total_records']} test records")
    logger.info(f"User distribution: {validation_results['user_distribution']}")
    
    # Export test records
    output_dir = Path("reports/integration_health_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"test_data_{config.integration_type}_{test_run_id}.json"
    
    factory.export_test_records(test_records, str(output_file))
    logger.info(f"Test data exported to: {output_file}")
    
    if dry_run:
        logger.info("DRY RUN: Test data generation completed without sending webhooks")
        return
    
    # Send webhooks
    logger.info("Sending webhooks...")
    webhook_validator = WebhookValidator(config)
    
    # Validate endpoint first
    endpoint_validation = webhook_validator.validate_webhook_endpoint()
    if not endpoint_validation['endpoint_reachable']:
        logger.error(f"Webhook endpoint validation failed: {endpoint_validation.get('error')}")
        return
    
    logger.info(f"Webhook endpoint validated successfully ({endpoint_validation['response_time']:.2f}s)")
    
    # Send bulk webhooks
    webhook_responses = webhook_validator.send_bulk_webhooks_sync(test_records)
    
    # Generate delivery report
    delivery_report_file = output_dir / f"webhook_delivery_{config.integration_type}_{test_run_id}.json"
    delivery_report = webhook_validator.generate_delivery_report(
        webhook_responses, 
        str(delivery_report_file)
    )
    
    # Log summary
    summary = delivery_report['summary']
    logger.info(f"Webhook delivery completed:")
    logger.info(f"  Total requests: {summary['total_requests']}")
    logger.info(f"  Successful: {summary['successful_requests']} ({summary['success_rate_percent']:.1f}%)")
    logger.info(f"  Failed: {summary['failed_requests']}")
    logger.info(f"  Average response time: {summary['avg_response_time_seconds']:.3f}s")
    
    if summary['failed_requests'] > 0:
        logger.warning("Some webhook deliveries failed. Check the delivery report for details.")
    
    logger.info(f"Delivery report saved to: {delivery_report_file}")
    logger.info(f"Next step: Wait {config.processing_delay}s then run integration validation")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate bulk test data for integration testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate test data with default config
  python scripts/bulk_test_generator.py
  
  # Use custom config file
  python scripts/bulk_test_generator.py --config tests/configs/custom_config.yaml
  
  # Dry run (generate data without sending webhooks)
  python scripts/bulk_test_generator.py --dry-run
  
  # Override number of test records
  python scripts/bulk_test_generator.py --test-records 50
        """
    )
    
    parser.add_argument(
        '--config',
        default='tests/configs/monitorbase_test_config.yaml',
        help='Path to test configuration file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate test data without sending webhooks'
    )
    
    parser.add_argument(
        '--test-records',
        type=int,
        help='Override number of test records to generate'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        
        # Override test records if specified
        if args.test_records:
            config.test_records = args.test_records
            logger.info(f"Override: Using {args.test_records} test records")
        
        # Load payload template
        logger.info(f"Loading payload template for: {config.integration_type}")
        payload_template = load_payload_template(config.integration_type)
        
        # Generate test data
        generate_test_data(config, payload_template, args.dry_run)
        
        logger.info("Test data generation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test data generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()