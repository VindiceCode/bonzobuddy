#!/usr/bin/env python3
"""
Integration health check script for monitoring integration status.
"""

import argparse
import json
import logging
import sys
import yaml
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tests.conftest import TestConfig, TestUser, ValidationRule
from scripts.bonzo_api_client import BonzoAPIClient, BonzoAPIError
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


def check_webhook_health(config: TestConfig) -> Dict[str, Any]:
    """Check webhook endpoint health."""
    logger.info("Checking webhook endpoint health...")
    
    webhook_validator = WebhookValidator(config)
    health_results = webhook_validator.validate_webhook_endpoint()
    
    health_status = {
        'webhook_url': config.webhook_url,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'healthy' if health_results['endpoint_reachable'] else 'unhealthy',
        'response_time': health_results.get('response_time', 0),
        'details': health_results
    }
    
    if health_results['endpoint_reachable']:
        logger.info(f"✓ Webhook endpoint healthy ({health_results['response_time']:.3f}s)")
    else:
        logger.error(f"✗ Webhook endpoint unhealthy: {health_results.get('error', 'Unknown error')}")
    
    return health_status


def check_api_connectivity(config: TestConfig) -> Dict[str, Any]:
    """Check Bonzo API connectivity and authentication."""
    logger.info("Checking Bonzo API connectivity...")
    
    api_client = BonzoAPIClient(config.superuser_api_key)
    api_status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'unknown',
        'users_accessible': 0,
        'total_users': len(config.test_users),
        'user_details': []
    }
    
    accessible_users = 0
    
    for user in config.test_users:
        user_status = {
            'user_id': user.user_id,
            'email': user.email,
            'accessible': False,
            'error': None,
            'prospect_count': 0
        }
        
        try:
            # Test API access for this user
            prospects = api_client.get_user_prospects(user.user_id, limit=10)
            user_status['accessible'] = True
            user_status['prospect_count'] = len(prospects)
            accessible_users += 1
            
            logger.info(f"✓ User {user.email} accessible ({len(prospects)} prospects)")
            
        except BonzoAPIError as e:
            user_status['error'] = str(e)
            logger.error(f"✗ User {user.email} not accessible: {e}")
        except Exception as e:
            user_status['error'] = f"Unexpected error: {str(e)}"
            logger.error(f"✗ User {user.email} check failed: {e}")
        
        api_status['user_details'].append(user_status)
    
    api_status['users_accessible'] = accessible_users
    api_status['status'] = 'healthy' if accessible_users == len(config.test_users) else 'partial' if accessible_users > 0 else 'unhealthy'
    
    logger.info(f"API connectivity: {accessible_users}/{len(config.test_users)} users accessible")
    
    return api_status


def check_recent_test_data(config: TestConfig, hours_back: int = 24) -> Dict[str, Any]:
    """Check for recent test data in Bonzo."""
    logger.info(f"Checking for test data from last {hours_back} hours...")
    
    api_client = BonzoAPIClient(config.superuser_api_key)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    test_data_status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'cutoff_time': cutoff_time.isoformat(),
        'hours_back': hours_back,
        'total_test_prospects': 0,
        'user_breakdown': []
    }
    
    total_test_prospects = 0
    
    for user in config.test_users:
        user_test_data = {
            'user_id': user.user_id,
            'email': user.email,
            'test_prospects_found': 0,
            'error': None
        }
        
        try:
            # Look for test prospects
            test_prospects = api_client.find_test_prospects(
                user.user_id,
                f"TestRecord_{config.integration_type.title()}",
                created_after=cutoff_time.isoformat()
            )
            
            user_test_data['test_prospects_found'] = len(test_prospects)
            total_test_prospects += len(test_prospects)
            
            if len(test_prospects) > 0:
                logger.info(f"✓ Found {len(test_prospects)} test prospects for {user.email}")
            else:
                logger.info(f"- No test prospects found for {user.email}")
            
        except Exception as e:
            user_test_data['error'] = str(e)
            logger.error(f"✗ Error checking test data for {user.email}: {e}")
        
        test_data_status['user_breakdown'].append(user_test_data)
    
    test_data_status['total_test_prospects'] = total_test_prospects
    logger.info(f"Total test prospects found: {total_test_prospects}")
    
    return test_data_status


def run_integration_health_check(config: TestConfig, check_test_data: bool = True) -> Dict[str, Any]:
    """Run comprehensive integration health check."""
    logger.info(f"Starting integration health check for {config.integration_type}")
    logger.info(f"Test configuration: {config.test_name}")
    
    health_report = {
        'integration_type': config.integration_type,
        'test_name': config.test_name,
        'check_timestamp': datetime.now(timezone.utc).isoformat(),
        'overall_status': 'unknown',
        'checks': {}
    }
    
    try:
        # Check webhook health
        webhook_health = check_webhook_health(config)
        health_report['checks']['webhook_health'] = webhook_health
        
        # Check API connectivity
        api_health = check_api_connectivity(config)
        health_report['checks']['api_connectivity'] = api_health
        
        # Check recent test data if requested
        if check_test_data:
            test_data_health = check_recent_test_data(config)
            health_report['checks']['recent_test_data'] = test_data_health
        
        # Determine overall status
        webhook_ok = webhook_health['status'] == 'healthy'
        api_ok = api_health['status'] == 'healthy'
        
        if webhook_ok and api_ok:
            health_report['overall_status'] = 'healthy'
        elif webhook_ok or api_ok:
            health_report['overall_status'] = 'partial'
        else:
            health_report['overall_status'] = 'unhealthy'
        
        logger.info(f"Integration health check completed: {health_report['overall_status']}")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_report['overall_status'] = 'error'
        health_report['error'] = str(e)
    
    return health_report


def save_health_report(health_report: Dict[str, Any], output_file: Optional[str] = None) -> str:
    """Save health report to file."""
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        integration_type = health_report.get('integration_type', 'unknown')
        output_file = f"reports/integration_health_reports/health_check_{integration_type}_{timestamp}.json"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    logger.info(f"Health report saved to: {output_path}")
    return str(output_path)


def print_health_summary(health_report: Dict[str, Any]) -> None:
    """Print a summary of the health check results."""
    print("\n" + "="*60)
    print(f"INTEGRATION HEALTH SUMMARY")
    print("="*60)
    print(f"Integration: {health_report['integration_type']}")
    print(f"Overall Status: {health_report['overall_status'].upper()}")
    print(f"Check Time: {health_report['check_timestamp']}")
    print()
    
    for check_name, check_data in health_report.get('checks', {}).items():
        status = check_data.get('status', 'unknown')
        status_symbol = {
            'healthy': '✓',
            'partial': '⚠',
            'unhealthy': '✗',
            'unknown': '?'
        }.get(status, '?')
        
        print(f"{status_symbol} {check_name.replace('_', ' ').title()}: {status.upper()}")
        
        if check_name == 'webhook_health':
            response_time = check_data.get('response_time', 0)
            print(f"    Response Time: {response_time:.3f}s")
            
        elif check_name == 'api_connectivity':
            accessible = check_data.get('users_accessible', 0)
            total = check_data.get('total_users', 0)
            print(f"    Users Accessible: {accessible}/{total}")
            
        elif check_name == 'recent_test_data':
            prospects = check_data.get('total_test_prospects', 0)
            hours = check_data.get('hours_back', 24)
            print(f"    Test Prospects ({hours}h): {prospects}")
    
    print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check integration health and connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run health check with default config
  python scripts/integration_health_check.py
  
  # Use custom config file
  python scripts/integration_health_check.py --config tests/configs/custom_config.yaml
  
  # Skip test data check
  python scripts/integration_health_check.py --no-test-data
  
  # Save to specific output file
  python scripts/integration_health_check.py --output health_report.json
        """
    )
    
    parser.add_argument(
        '--config',
        default='tests/configs/monitorbase_test_config.yaml',
        help='Path to test configuration file'
    )
    
    parser.add_argument(
        '--no-test-data',
        action='store_true',
        help='Skip checking for recent test data'
    )
    
    parser.add_argument(
        '--test-data-hours',
        type=int,
        default=24,
        help='Hours back to check for test data (default: 24)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for health report'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress summary output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        
        # Run health check
        health_report = run_integration_health_check(
            config, 
            check_test_data=not args.no_test_data
        )
        
        # Save report
        output_file = save_health_report(health_report, args.output)
        
        # Print summary unless quiet
        if not args.quiet:
            print_health_summary(health_report)
        
        # Exit with appropriate code
        status = health_report['overall_status']
        if status == 'healthy':
            sys.exit(0)
        elif status == 'partial':
            sys.exit(1)
        else:
            sys.exit(2)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(4)


if __name__ == '__main__':
    main()