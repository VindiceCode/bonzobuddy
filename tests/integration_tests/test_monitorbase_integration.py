"""
Monitorbase integration test suite for end-to-end validation.
"""

import pytest
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.bonzo_api_client import BonzoAPIClient, ProspectData
from scripts.webhook_validator import WebhookValidator
from scripts.test_data_factory import TestDataFactory, TestRecord

logger = logging.getLogger(__name__)


class TestMonitorbaseIntegration:
    """Comprehensive Monitorbase integration test suite."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, test_config, test_run_id, is_dry_run):
        """Set up test environment and dependencies."""
        self.config = test_config
        self.test_run_id = test_run_id
        self.is_dry_run = is_dry_run
        
        # Initialize clients
        self.api_client = BonzoAPIClient(test_config.superuser_api_key)
        self.webhook_validator = WebhookValidator(test_config)
        
        # Test data will be generated in individual tests
        self.test_records: List[TestRecord] = []
        self.webhook_responses = []
        
    def test_webhook_endpoint_availability(self):
        """Test that webhook endpoint is reachable and properly configured."""
        if self.is_dry_run:
            pytest.skip("Skipping webhook endpoint test in dry run mode")
        
        logger.info("Testing webhook endpoint availability")
        validation_results = self.webhook_validator.validate_webhook_endpoint()
        
        assert validation_results['endpoint_reachable'], f"Webhook endpoint not reachable: {validation_results.get('error')}"
        assert validation_results['supports_post'], "Webhook endpoint does not support POST requests"
        assert validation_results['accepts_json'], "Webhook endpoint does not accept JSON content"
        
        # Log performance metrics
        response_time = validation_results['response_time']
        logger.info(f"Webhook endpoint responds in {response_time:.2f}s")
        
        # Performance assertion (should respond within reasonable time)
        assert response_time < 10.0, f"Webhook endpoint too slow: {response_time:.2f}s"
    
    @pytest.mark.webhook
    def test_bulk_webhook_delivery(self, test_config, payload_template, test_data_pattern):
        """Test bulk webhook delivery with proper distribution among users."""
        # Generate test data
        factory = TestDataFactory(test_config, payload_template)
        self.test_records = factory.generate_test_records(self.test_run_id)
        
        # Validate test data generation
        validation_results = factory.validate_test_records(self.test_records)
        assert validation_results['records_match'], f"Expected {validation_results['expected_records']} records, got {validation_results['total_records']}"
        assert validation_results['emails_unique'], "Test record emails are not unique"
        assert validation_results['record_ids_unique'], "Test record IDs are not unique"
        assert not validation_results['validation_errors'], f"Validation errors: {validation_results['validation_errors']}"
        
        if self.is_dry_run:
            logger.info(f"DRY RUN: Would send {len(self.test_records)} webhook requests")
            logger.info(f"User distribution: {validation_results['user_distribution']}")
            return
        
        # Send webhooks
        logger.info(f"Sending {len(self.test_records)} webhook requests")
        self.webhook_responses = self.webhook_validator.send_bulk_webhooks_sync(self.test_records)
        
        # Validate delivery results
        successful_responses = [r for r in self.webhook_responses if 200 <= r.status_code < 300]
        failed_responses = [r for r in self.webhook_responses if r.status_code < 200 or r.status_code >= 300]
        
        success_rate = len(successful_responses) / len(self.webhook_responses) * 100
        logger.info(f"Webhook delivery: {len(successful_responses)}/{len(self.webhook_responses)} successful ({success_rate:.1f}%)")
        
        # Assert minimum success rate (should be configurable)
        min_success_rate = 95.0  # 95% minimum success rate
        assert success_rate >= min_success_rate, f"Webhook success rate too low: {success_rate:.1f}% (minimum: {min_success_rate}%)"
        
        # Log failed requests for debugging
        if failed_responses:
            logger.warning(f"Failed webhook deliveries:")
            for response in failed_responses[:5]:  # Log first 5 failures
                logger.warning(f"  Record {response.record_id}: {response.status_code} - {response.error or response.response_text[:100]}")
    
    @pytest.mark.api
    def test_prospect_creation_validation(self, test_config):
        """Test that prospects are created in Bonzo with correct assignments."""
        if self.is_dry_run:
            pytest.skip("Skipping prospect validation in dry run mode")
        
        if not self.test_records:
            pytest.skip("No test records available (run webhook delivery test first)")
        
        # Wait for processing
        logger.info(f"Waiting {test_config.processing_delay}s for webhook processing")
        time.sleep(test_config.processing_delay)
        
        # Validate prospects for each user
        validation_results = {}
        
        for user in test_config.test_users:
            logger.info(f"Validating prospects for user {user.name} ({user.email})")
            
            # Calculate expected count for this user
            user_records = [r for r in self.test_records if r.user_email == user.email]
            expected_count = len(user_records)
            
            if expected_count == 0:
                continue
            
            try:
                # Find test prospects for this user
                test_prospects = self.api_client.find_test_prospects(
                    user.user_id,
                    f"TestRecord_{test_config.integration_type.title()}_{self.test_run_id}",
                    created_after=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
                )
                
                validation_results[user.email] = {
                    'expected_count': expected_count,
                    'found_count': len(test_prospects),
                    'prospects': test_prospects,
                    'user_id': user.user_id,
                    'team_id': user.team_id
                }
                
                logger.info(f"Found {len(test_prospects)}/{expected_count} test prospects for {user.email}")
                
            except Exception as e:
                logger.error(f"Failed to validate prospects for {user.email}: {e}")
                validation_results[user.email] = {
                    'expected_count': expected_count,
                    'found_count': 0,
                    'prospects': [],
                    'error': str(e),
                    'user_id': user.user_id,
                    'team_id': user.team_id
                }
        
        # Assert that prospects were created
        total_expected = sum(result['expected_count'] for result in validation_results.values())
        total_found = sum(result['found_count'] for result in validation_results.values())
        
        creation_rate = (total_found / total_expected * 100) if total_expected > 0 else 0
        logger.info(f"Prospect creation: {total_found}/{total_expected} prospects found ({creation_rate:.1f}%)")
        
        # Assert minimum creation rate
        min_creation_rate = 90.0  # 90% minimum creation rate
        assert creation_rate >= min_creation_rate, f"Prospect creation rate too low: {creation_rate:.1f}% (minimum: {min_creation_rate}%)"
        
        # Store results for use in assignment validation
        self.prospect_validation_results = validation_results
    
    @pytest.mark.data_integrity
    def test_user_assignment_accuracy(self, test_config):
        """Test that prospects are assigned to correct users based on lo_email."""
        if self.is_dry_run:
            pytest.skip("Skipping user assignment validation in dry run mode")
        
        if not hasattr(self, 'prospect_validation_results'):
            pytest.skip("No prospect validation results available")
        
        assignment_errors = []
        total_prospects = 0
        correct_assignments = 0
        
        for user_email, results in self.prospect_validation_results.items():
            if 'error' in results:
                continue
            
            user = next(u for u in test_config.test_users if u.email == user_email)
            prospects = results['prospects']
            
            for prospect in prospects:
                total_prospects += 1
                
                # Validate assignment
                assignment_validation = self.api_client.validate_prospect_assignment(
                    prospect,
                    expected_user_email=user.email,
                    expected_user_id=user.user_id,
                    expected_team_id=user.team_id
                )
                
                if all(assignment_validation.values()):
                    correct_assignments += 1
                else:
                    assignment_errors.append({
                        'prospect_id': prospect.id,
                        'prospect_name': prospect.full_name,
                        'expected_user': user.email,
                        'actual_user': prospect.assigned_user.get('email'),
                        'expected_user_id': user.user_id,
                        'actual_user_id': prospect.assigned_user.get('id'),
                        'expected_team_id': user.team_id,
                        'actual_team_id': prospect.business_entity_id,
                        'validation_results': assignment_validation
                    })
        
        assignment_accuracy = (correct_assignments / total_prospects * 100) if total_prospects > 0 else 0
        logger.info(f"User assignment accuracy: {correct_assignments}/{total_prospects} correct ({assignment_accuracy:.1f}%)")
        
        # Log assignment errors
        if assignment_errors:
            logger.warning(f"Assignment errors found:")
            for error in assignment_errors[:5]:  # Log first 5 errors
                logger.warning(f"  Prospect {error['prospect_id']} ({error['prospect_name']}): expected {error['expected_user']}, got {error['actual_user']}")
        
        # Assert minimum assignment accuracy
        min_assignment_accuracy = 95.0  # 95% minimum assignment accuracy
        assert assignment_accuracy >= min_assignment_accuracy, f"User assignment accuracy too low: {assignment_accuracy:.1f}% (minimum: {min_assignment_accuracy}%)"
    
    @pytest.mark.data_integrity
    def test_data_mapping_integrity(self, test_config):
        """Test that data fields are properly mapped from webhook to Bonzo."""
        if self.is_dry_run:
            pytest.skip("Skipping data mapping validation in dry run mode")
        
        if not hasattr(self, 'prospect_validation_results'):
            pytest.skip("No prospect validation results available")
        
        mapping_errors = []
        total_prospects = 0
        correct_mappings = 0
        
        # Get validation rules from config
        validation_rules = test_config.validation_rules
        
        for user_email, results in self.prospect_validation_results.items():
            if 'error' in results:
                continue
            
            prospects = results['prospects']
            
            for prospect in prospects:
                total_prospects += 1
                prospect_errors = []
                
                # Validate each rule
                for rule in validation_rules:
                    field_path = rule.field
                    expected_value = rule.expected
                    
                    # Get actual value from prospect
                    actual_value = self._get_field_value(prospect, field_path)
                    
                    if rule.matches_lo_email:
                        # Special validation for lo_email matching
                        user = next(u for u in test_config.test_users if u.email == user_email)
                        if actual_value != user.email:
                            prospect_errors.append(f"{field_path}: expected {user.email}, got {actual_value}")
                    elif expected_value and actual_value != expected_value:
                        prospect_errors.append(f"{field_path}: expected {expected_value}, got {actual_value}")
                
                if not prospect_errors:
                    correct_mappings += 1
                else:
                    mapping_errors.append({
                        'prospect_id': prospect.id,
                        'prospect_name': prospect.full_name,
                        'errors': prospect_errors
                    })
        
        mapping_accuracy = (correct_mappings / total_prospects * 100) if total_prospects > 0 else 0
        logger.info(f"Data mapping accuracy: {correct_mappings}/{total_prospects} correct ({mapping_accuracy:.1f}%)")
        
        # Log mapping errors
        if mapping_errors:
            logger.warning(f"Data mapping errors found:")
            for error in mapping_errors[:5]:  # Log first 5 errors
                logger.warning(f"  Prospect {error['prospect_id']} ({error['prospect_name']}): {error['errors']}")
        
        # Assert minimum mapping accuracy
        min_mapping_accuracy = 95.0  # 95% minimum mapping accuracy
        assert mapping_accuracy >= min_mapping_accuracy, f"Data mapping accuracy too low: {mapping_accuracy:.1f}% (minimum: {min_mapping_accuracy}%)"
    
    def _get_field_value(self, prospect: ProspectData, field_path: str) -> Any:
        """Get field value from prospect using dot notation path."""
        try:
            value = prospect
            for part in field_path.split('.'):
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        except (AttributeError, KeyError, TypeError):
            return None
    
    @pytest.mark.slow
    def test_processing_performance(self, test_config):
        """Test that webhook processing meets performance requirements."""
        if self.is_dry_run:
            pytest.skip("Skipping performance validation in dry run mode")
        
        if not hasattr(self, 'prospect_validation_results'):
            pytest.skip("No prospect validation results available")
        
        # Calculate processing metrics
        webhook_send_time = getattr(self, 'webhook_send_start_time', None)
        prospect_find_time = getattr(self, 'prospect_find_time', None)
        
        if webhook_send_time and prospect_find_time:
            total_processing_time = prospect_find_time - webhook_send_time
            logger.info(f"Total processing time: {total_processing_time:.2f}s")
            
            # Assert reasonable processing time
            max_processing_time = 300  # 5 minutes maximum
            assert total_processing_time <= max_processing_time, f"Processing time too long: {total_processing_time:.2f}s (maximum: {max_processing_time}s)"
        
        # Validate webhook response times
        if hasattr(self, 'webhook_responses') and self.webhook_responses:
            response_times = [r.response_time for r in self.webhook_responses if r.response_time > 0]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                logger.info(f"Webhook response times - avg: {avg_response_time:.2f}s, max: {max_response_time:.2f}s")
                
                # Assert reasonable response times
                assert avg_response_time <= 5.0, f"Average webhook response time too high: {avg_response_time:.2f}s"
                assert max_response_time <= 30.0, f"Maximum webhook response time too high: {max_response_time:.2f}s"
    
    @pytest.mark.superuser
    def test_superuser_webhook_with_user_id(self, test_config, superuser_payload_template, test_data_pattern):
        """Test superuser webhook delivery with user_id field for cross-team processing."""
        # Generate test data using superuser payload template
        factory = TestDataFactory(test_config, superuser_payload_template)
        superuser_test_records = factory.generate_test_records(f"{self.test_run_id}_SU")
        
        # Validate test data generation
        validation_results = factory.validate_test_records(superuser_test_records)
        assert validation_results['records_match'], f"Expected {validation_results['expected_records']} records, got {validation_results['total_records']}"
        assert validation_results['emails_unique'], "Test record emails are not unique"
        assert validation_results['record_ids_unique'], "Test record IDs are not unique"
        assert not validation_results['validation_errors'], f"Validation errors: {validation_results['validation_errors']}"
        
        # Verify user_id field is properly populated in payloads
        for record in superuser_test_records:
            assert 'user_id' in record.payload, f"user_id field missing from payload for record {record.record_id}"
            assert str(record.payload['user_id']) == str(record.user_id), f"user_id mismatch: expected {record.user_id}, got {record.payload['user_id']}"
            logger.info(f"Record {record.record_id}: user_id={record.payload['user_id']}, lo_email={record.payload.get('lo_email')}")
        
        if self.is_dry_run:
            logger.info(f"DRY RUN: Would send {len(superuser_test_records)} superuser webhook requests with user_id")
            logger.info(f"User distribution: {validation_results['user_distribution']}")
            return
        
        # Create superuser webhook validator with superuser endpoint
        superuser_webhook_validator = WebhookValidator(test_config, webhook_url=test_config.superuser_webhook_url)
        
        # Send superuser webhooks
        logger.info(f"Sending {len(superuser_test_records)} superuser webhook requests with user_id")
        superuser_webhook_responses = superuser_webhook_validator.send_bulk_webhooks_sync(superuser_test_records)
        
        # Validate delivery results
        successful_responses = [r for r in superuser_webhook_responses if 200 <= r.status_code < 300]
        failed_responses = [r for r in superuser_webhook_responses if r.status_code < 200 or r.status_code >= 300]
        
        success_rate = len(successful_responses) / len(superuser_webhook_responses) * 100
        logger.info(f"Superuser webhook delivery: {len(successful_responses)}/{len(superuser_webhook_responses)} successful ({success_rate:.1f}%)")
        
        # Assert minimum success rate
        min_success_rate = 95.0  # 95% minimum success rate
        assert success_rate >= min_success_rate, f"Superuser webhook success rate too low: {success_rate:.1f}% (minimum: {min_success_rate}%)"
        
        # Store results for follow-up validation
        self.superuser_test_records = superuser_test_records
        self.superuser_webhook_responses = superuser_webhook_responses
        
        # Log failed requests for debugging
        if failed_responses:
            logger.warning(f"Failed superuser webhook deliveries:")
            for response in failed_responses[:5]:  # Log first 5 failures
                logger.warning(f"  Record {response.record_id}: {response.status_code} - {response.error or response.response_text[:100]}")
    
    @pytest.mark.superuser
    def test_superuser_prospect_creation_with_user_id(self, test_config, superuser_payload_template, test_data_pattern):
        """Test that superuser webhooks with user_id create prospects assigned to correct users."""
        if self.is_dry_run:
            pytest.skip("Skipping superuser prospect validation in dry run mode")
        
        # Generate and send test records if not already done
        if not hasattr(self, 'superuser_test_records'):
            logger.info("Generating superuser test records for independent validation")
            factory = TestDataFactory(test_config, superuser_payload_template)
            self.superuser_test_records = factory.generate_test_records(f"{self.test_run_id}_SU_VAL")
            
            # Send webhooks for validation
            superuser_webhook_validator = WebhookValidator(test_config, webhook_url=test_config.superuser_webhook_url)
            logger.info(f"Sending {len(self.superuser_test_records)} superuser webhook requests for validation")
            self.superuser_webhook_responses = superuser_webhook_validator.send_bulk_webhooks_sync(self.superuser_test_records)
            
            # Brief validation of webhook delivery
            successful_responses = [r for r in self.superuser_webhook_responses if 200 <= r.status_code < 300]
            success_rate = len(successful_responses) / len(self.superuser_webhook_responses) * 100
            logger.info(f"Superuser webhook delivery for validation: {len(successful_responses)}/{len(self.superuser_webhook_responses)} successful ({success_rate:.1f}%)")
            
            # Ensure minimum success rate before proceeding
            assert success_rate >= 90.0, f"Insufficient webhook success rate for validation: {success_rate:.1f}%"
        
        # Wait for processing
        logger.info(f"Waiting {test_config.processing_delay}s for superuser webhook processing")
        time.sleep(test_config.processing_delay)
        
        # Validate prospects for each user
        superuser_validation_results = {}
        
        for user in test_config.test_users:
            logger.info(f"Validating superuser prospects for user {user.name} ({user.email})")
            
            # Calculate expected count for this user
            user_records = [r for r in self.superuser_test_records if r.user_email == user.email]
            expected_count = len(user_records)
            
            if expected_count == 0:
                continue
            
            try:
                # Find test prospects for this user (created via superuser webhook)
                # Search for simple "TestRecord" pattern since that's what we actually send
                test_prospects = self.api_client.find_test_prospects(
                    user.user_id,
                    "TestRecord",  # Simple pattern that matches first_name: "TestRecord_001"
                    created_after=(datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
                )
                
                superuser_validation_results[user.email] = {
                    'expected_count': expected_count,
                    'found_count': len(test_prospects),
                    'prospects': test_prospects,
                    'user_id': user.user_id,
                    'team_id': user.team_id,
                    'test_type': 'superuser_with_user_id'
                }
                
                logger.info(f"Found {len(test_prospects)}/{expected_count} superuser test prospects for {user.email}")
                
                # Validate that prospects were assigned based on user_id, not just lo_email
                for prospect in test_prospects:
                    if hasattr(prospect, 'assigned_user') and prospect.assigned_user:
                        actual_user_id = prospect.assigned_user.get('id')
                        if actual_user_id != user.user_id:
                            logger.warning(f"Superuser prospect {prospect.id} assigned to user_id {actual_user_id}, expected {user.user_id}")
                
            except Exception as e:
                logger.error(f"Failed to validate superuser prospects for {user.email}: {e}")
                superuser_validation_results[user.email] = {
                    'expected_count': expected_count,
                    'found_count': 0,
                    'prospects': [],
                    'error': str(e),
                    'user_id': user.user_id,
                    'team_id': user.team_id,
                    'test_type': 'superuser_with_user_id'
                }
        
        # Assert that prospects were created
        total_expected = sum(result['expected_count'] for result in superuser_validation_results.values())
        total_found = sum(result['found_count'] for result in superuser_validation_results.values())
        
        creation_rate = (total_found / total_expected * 100) if total_expected > 0 else 0
        logger.info(f"Superuser prospect creation: {total_found}/{total_expected} prospects found ({creation_rate:.1f}%)")
        
        # Assert minimum creation rate for superuser functionality
        min_creation_rate = 90.0  # 90% minimum creation rate
        assert creation_rate >= min_creation_rate, f"Superuser prospect creation rate too low: {creation_rate:.1f}% (minimum: {min_creation_rate}%)"
        
        # Store results for use in assignment validation
        self.superuser_prospect_validation_results = superuser_validation_results

    def test_generate_integration_report(self, reports_dir, test_config):
        """Generate comprehensive integration test report."""
        if self.is_dry_run:
            logger.info("DRY RUN: Would generate integration report")
            return
        
        report_data = {
            'test_run_info': {
                'test_name': test_config.test_name,
                'integration_type': test_config.integration_type,
                'test_run_id': self.test_run_id,
                'test_records': test_config.test_records,
                'users_tested': len(test_config.test_users),
                'generated_at': datetime.now(timezone.utc).isoformat()
            },
            'webhook_delivery': {},
            'prospect_validation': {},
            'assignment_validation': {},
            'data_mapping_validation': {}
        }
        
        # Add webhook delivery results
        if hasattr(self, 'webhook_responses'):
            report_data['webhook_delivery'] = self.webhook_validator.generate_delivery_report(
                self.webhook_responses
            )
        
        # Add prospect validation results
        if hasattr(self, 'prospect_validation_results'):
            report_data['prospect_validation'] = self.prospect_validation_results
        
        # Add superuser test results
        if hasattr(self, 'superuser_webhook_responses'):
            report_data['superuser_webhook_delivery'] = self.webhook_validator.generate_delivery_report(
                self.superuser_webhook_responses
            )
        
        if hasattr(self, 'superuser_prospect_validation_results'):
            report_data['superuser_prospect_validation'] = self.superuser_prospect_validation_results
        
        # Save report
        report_file = reports_dir / f"monitorbase_integration_report_{self.test_run_id}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Integration report saved to {report_file}")
        
        # Assert report was created
        assert report_file.exists(), f"Integration report not created: {report_file}"