"""
Test data factory for generating bulk test records.
"""

import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import string
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestRecord:
    """Individual test record data."""
    record_id: str
    user_email: str
    user_id: int
    team_id: int
    payload: Dict[str, Any]
    sequence_number: int


class TestDataFactory:
    """Factory for generating bulk test data records."""
    
    def __init__(self, config, payload_template: Dict[str, Any]):
        """
        Initialize test data factory.
        
        Args:
            config: Test configuration object
            payload_template: JSON payload template
        """
        self.config = config
        self.payload_template = payload_template
        self.test_data_settings = getattr(config, 'test_data_settings', {})
        
    def generate_test_records(self, test_run_id: str) -> List[TestRecord]:
        """
        Generate bulk test records according to configuration.
        
        Args:
            test_run_id: Unique identifier for this test run
            
        Returns:
            List of TestRecord objects
        """
        records = []
        
        # Distribute records among users
        user_distributions = self._calculate_user_distribution()
        
        record_counter = 1
        for user_index, count in user_distributions.items():
            user = self.config.test_users[user_index]  # Get user by index
            for i in range(count):
                record_id = f"{test_run_id}_{record_counter:03d}"
                
                test_record = TestRecord(
                    record_id=record_id,
                    user_email=user.email,
                    user_id=user.user_id,
                    team_id=user.team_id,
                    payload=self._generate_payload(user, record_id, record_counter),
                    sequence_number=record_counter
                )
                
                records.append(test_record)
                record_counter += 1
        
        logger.info(f"Generated {len(records)} test records for {len(user_distributions)} users")
        return records
    
    def _calculate_user_distribution(self) -> Dict[int, int]:
        """Calculate how many records each user should receive."""
        users = self.config.test_users
        total_records = self.config.test_records
        distribution_method = self.config.distribution
        
        user_distributions = {}
        
        if distribution_method == "even":
            # Distribute evenly among users
            base_count = total_records // len(users)
            remainder = total_records % len(users)
            
            for i, user in enumerate(users):
                count = base_count + (1 if i < remainder else 0)
                user_distributions[i] = count  # Use index instead of user object
                
        elif distribution_method == "weighted":
            # TODO: Implement weighted distribution based on user weights
            # For now, fall back to even distribution
            return self._calculate_user_distribution_even(total_records)
            
        elif distribution_method == "custom":
            # TODO: Implement custom distribution based on user-specified counts
            # For now, fall back to even distribution
            return self._calculate_user_distribution_even(total_records)
            
        else:
            raise ValueError(f"Unknown distribution method: {distribution_method}")
        
        logger.info(f"Distribution: {[(self.config.test_users[i].name, count) for i, count in user_distributions.items()]}")
        return user_distributions
    
    def _calculate_user_distribution_even(self, total_records):
        """Helper method for even distribution."""
        users = self.config.test_users
        user_distributions = {}
        base_count = total_records // len(users)
        remainder = total_records % len(users)
        
        for i, user in enumerate(users):
            count = base_count + (1 if i < remainder else 0)
            user_distributions[i] = count  # Use index instead of user object
            
        return user_distributions
    
    def _generate_payload(self, user, record_id: str, sequence_number: int) -> Dict[str, Any]:
        """
        Generate payload for a single test record.
        
        Args:
            user: TestUser object
            record_id: Unique record identifier
            sequence_number: Sequential number for this record
            
        Returns:
            Generated payload dictionary
        """
        # Start with template
        payload = json.loads(json.dumps(self.payload_template))
        
        # Generate test data
        test_data = self._generate_test_data(record_id, sequence_number)
        
        # Replace template variables
        payload = self._replace_template_variables(payload, user, test_data, record_id)
        
        return payload
    
    def _generate_test_data(self, record_id: str, sequence_number: int) -> Dict[str, Any]:
        """Generate random test data for a record."""
        settings = self.test_data_settings
        
        # Generate unique identifiers
        unique_suffix = f"{sequence_number:03d}"
        
        # Generate names
        first_name_pattern = settings.get('first_name_pattern', 'TestRecord')
        last_name_pattern = settings.get('last_name_pattern', 'Test')
        
        first_name = f"{first_name_pattern}_{unique_suffix}"
        last_name = f"{last_name_pattern}"
        
        # Generate email
        email_domain = settings.get('email_domain', 'bonzobuddy.test')
        email = f"test.{self.config.integration_type}.{unique_suffix}@{email_domain}"
        
        # Generate phone
        area_code = settings.get('phone_area_code', '555')
        phone_number = f"{area_code}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        # Generate address
        address_pattern = settings.get('address_pattern', '123 Test St')
        address = f"{random.randint(100, 9999)} {address_pattern.split()[1:]}"
        if isinstance(address, list):
            address = " ".join(address)
        
        city = settings.get('city', 'TestCity')
        state = settings.get('state', 'CA')
        zip_code = settings.get('zip', '12345')
        
        # Generate timestamps
        now = datetime.now(timezone.utc)
        alert_date = now.strftime('%Y-%m-%d')
        created_at = now.isoformat()
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone_number,
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'alert_date': alert_date,
            'created_at': created_at,
            'record_id': record_id
        }
    
    def _replace_template_variables(
        self, 
        payload: Dict[str, Any], 
        user, 
        test_data: Dict[str, Any],
        record_id: str
    ) -> Dict[str, Any]:
        """
        Replace template variables in payload with actual values.
        
        Args:
            payload: Payload dictionary with template variables
            user: TestUser object
            test_data: Generated test data
            record_id: Unique record identifier
            
        Returns:
            Payload with replaced variables
        """
        # Convert to JSON string for easy replacement
        payload_str = json.dumps(payload)
        
        # User-related replacements
        payload_str = payload_str.replace('{user.email}', user.email)
        payload_str = payload_str.replace('{user.id}', str(user.user_id))
        payload_str = payload_str.replace('{user.user_id}', str(user.user_id))
        payload_str = payload_str.replace('{team.id}', str(user.team_id))
        
        # Test data replacements
        for key, value in test_data.items():
            payload_str = payload_str.replace(f'{{{key}}}', str(value))
        
        # Record ID replacements
        payload_str = payload_str.replace('{record_id}', record_id)
        
        # Convert back to dictionary
        return json.loads(payload_str)
    
    def validate_test_records(self, records: List[TestRecord]) -> Dict[str, Any]:
        """
        Validate generated test records.
        
        Args:
            records: List of TestRecord objects
            
        Returns:
            Validation results dictionary
        """
        validation_results = {
            'total_records': len(records),
            'expected_records': self.config.test_records,
            'records_match': len(records) == self.config.test_records,
            'user_distribution': {},
            'unique_emails': set(),
            'unique_record_ids': set(),
            'validation_errors': []
        }
        
        # Check user distribution
        for user in self.config.test_users:
            user_records = [r for r in records if r.user_email == user.email]
            validation_results['user_distribution'][user.email] = len(user_records)
        
        # Check for unique identifiers
        for record in records:
            validation_results['unique_emails'].add(record.payload.get('email', ''))
            validation_results['unique_record_ids'].add(record.record_id)
            
            # Validate required fields
            if not record.payload.get('first_name'):
                validation_results['validation_errors'].append(f"Missing first_name in record {record.record_id}")
            
            # Check for either lo_email (Monitorbase format) or email (standard format)
            if not record.payload.get('lo_email') and not record.payload.get('email'):
                validation_results['validation_errors'].append(f"Missing email field in record {record.record_id}")
            
            # For superuser payloads, validate user_id is present
            if 'user_id' in record.payload and not record.payload.get('user_id'):
                validation_results['validation_errors'].append(f"Missing user_id in record {record.record_id}")
        
        # Check uniqueness
        validation_results['emails_unique'] = len(validation_results['unique_emails']) == len(records)
        validation_results['record_ids_unique'] = len(validation_results['unique_record_ids']) == len(records)
        
        # Convert sets to lists for JSON serialization
        validation_results['unique_emails'] = list(validation_results['unique_emails'])
        validation_results['unique_record_ids'] = list(validation_results['unique_record_ids'])
        
        logger.info(f"Validation results: {len(validation_results['validation_errors'])} errors found")
        return validation_results
    
    def export_test_records(self, records: List[TestRecord], output_file: str) -> None:
        """
        Export test records to JSON file.
        
        Args:
            records: List of TestRecord objects
            output_file: Output file path
        """
        export_data = {
            'test_run_info': {
                'integration_type': self.config.integration_type,
                'test_name': self.config.test_name,
                'total_records': len(records),
                'users': [
                    {
                        'name': user.name,
                        'email': user.email,
                        'user_id': user.user_id,
                        'team_id': user.team_id
                    }
                    for user in self.config.test_users
                ],
                'generated_at': datetime.now(timezone.utc).isoformat()
            },
            'test_records': [
                {
                    'record_id': record.record_id,
                    'user_email': record.user_email,
                    'user_id': record.user_id,
                    'team_id': record.team_id,
                    'sequence_number': record.sequence_number,
                    'payload': record.payload
                }
                for record in records
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(records)} test records to {output_file}")


def create_test_data_factory(config, payload_template: Dict[str, Any]) -> TestDataFactory:
    """
    Factory function to create TestDataFactory instance.
    
    Args:
        config: Test configuration object
        payload_template: JSON payload template
        
    Returns:
        TestDataFactory instance
    """
    return TestDataFactory(config, payload_template)