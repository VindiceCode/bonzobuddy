# Bulk Integration Testing Framework

## Overview

A comprehensive testing framework for validating end-to-end integration health in Bonzo Buddy. This terminal-based solution enables bulk webhook testing, automated validation, and visual reporting using pytest.

## Core Concept

The framework sends bulk test records to webhook endpoints, validates successful integration through Bonzo's API, and provides detailed reporting on integration health and data integrity.

## Architecture

### Test Flow
1. **Bulk Data Generation**: Create configurable number of test records with identifiable patterns
2. **Webhook Delivery**: Send test payloads to target webhook endpoints
3. **Processing Wait**: Allow time for webhook processing and data ingestion
4. **API Validation**: Query Bonzo API to verify record creation and assignment
5. **Report Generation**: Generate pytest HTML reports with pass/fail metrics

### Configuration-Driven Testing

Test scenarios are defined in YAML configuration files:

```yaml
# test_config.yaml
test_name: "Monitorbase Integration Test"
webhook_url: "{TEST_HOOK_URL}"
superuser_api_key: "{SUPERUSER_API_KEY}"
integration_type: "monitorbase"
test_records: 21
distribution: "even"
processing_delay: 30  # seconds to wait before validation

test_users:
  - name: "RevTeamUser1"
    email: "escuderi@revolutionmortgage.com"
    user_id: 65013
    team_id: 12779
  - name: "RevTeamUser2"
    email: "emorgan@revolutionmortgage.com"
    user_id: 27227
    team_id: 12211
  - name: "RevTeamUser3"
    email: "mrocco@revolutionmortgage.com"
    user_id: 29194
    team_id: 12896

validation_rules:
  - field: "source"
    expected: "monitorbase"
  - field: "assigned_user.email"
    matches_lo_email: true
```

## Test Categories

### 1. Webhook Delivery Testing
- Validates webhook endpoint availability
- Tests bulk payload acceptance
- Measures response times and success rates
- Identifies delivery failures

### 2. End-to-End Integration Testing
- Verifies complete data flow from webhook to Bonzo
- Validates lo_email → user_id resolution
- Confirms proper team assignment
- Tests data persistence

### 3. Data Integrity Testing
- Validates field mapping accuracy
- Confirms required field population
- Tests custom field handling
- Verifies data transformation correctness

### 4. Business Logic Testing
- Tests user assignment logic
- Validates team-based routing
- Confirms superuser on-behalf-of functionality
- Tests prospect ownership rules

## Implementation Structure

```
tests/
├── conftest.py                           # Pytest configuration and fixtures
├── integration_tests/
│   ├── __init__.py
│   ├── test_monitorbase_integration.py   # Monitorbase-specific tests
│   ├── test_webhook_delivery.py          # Generic webhook testing
│   └── test_data_integrity.py            # Data validation tests
├── configs/
│   ├── monitorbase_test_config.yaml      # Monitorbase test configuration
│   └── test_config_template.yaml         # Template for new integrations
└── fixtures/
    ├── monitorbase_payload_template.json # Payload templates
    └── expected_responses.json            # Expected API responses

scripts/
├── __init__.py
├── bulk_test_generator.py                # Generate bulk test data
├── integration_health_check.py           # Standalone health monitoring
├── webhook_validator.py                  # Webhook testing utilities
├── bonzo_api_client.py                   # Bonzo API interaction
└── test_data_factory.py                  # Test data generation utilities

reports/                                  # Generated test reports
├── integration_health_reports/
└── pytest_html_reports/
```

## Test Data Patterns

### Identifiable Test Records
- **Naming Pattern**: `TestRecord_MonitorBase_001` through `TestRecord_MonitorBase_XXX`
- **Email Pattern**: `test.monitorbase.001@bonzobuddy.test`
- **Unique Identifiers**: Include timestamp and test run ID
- **Easy Cleanup**: Consistent naming for post-test cleanup

### Data Distribution
- **Even Distribution**: Split test records evenly among test users
- **Weighted Distribution**: Configurable weights per user
- **Custom Distribution**: Specify exact counts per user

## CLI Interface

### Test Execution Commands
```bash
# Run all integration tests
uv run python -m pytest tests/integration_tests/ -v --html=reports/integration_report.html

# Run specific integration tests
uv run python -m pytest tests/integration_tests/test_monitorbase_integration.py -v

# Generate bulk test data only
uv run python scripts/bulk_test_generator.py --config tests/configs/monitorbase_test_config.yaml

# Run standalone health check
uv run python scripts/integration_health_check.py --integration monitorbase --config tests/configs/monitorbase_test_config.yaml

# Cleanup test data
uv run python scripts/cleanup_test_data.py --pattern "TestRecord_MonitorBase_*"
```

### Configuration Options
```bash
# Custom test record count
uv run python -m pytest tests/integration_tests/ --test-records=50

# Custom processing delay
uv run python -m pytest tests/integration_tests/ --processing-delay=60

# Dry run mode (no actual webhook calls)
uv run python scripts/bulk_test_generator.py --dry-run --config tests/configs/monitorbase_test_config.yaml
```

## Reporting and Visualization

### Pytest HTML Reports
- Test execution summary with pass/fail counts
- Individual test case details with timing
- Error logs and stack traces
- Integration health metrics dashboard

### Integration Health Dashboard
- Webhook delivery success rate
- Data integrity validation results
- Performance metrics and trends
- User assignment accuracy

### Test Data Metrics
- Records sent vs. records created
- Processing time analysis
- Error categorization and frequency
- Data mapping accuracy scores

## Business Requirements Validation

### Monitorbase Integration Requirements
1. **User Resolution**: `lo_email` must correctly resolve to `user_id`
2. **Team Assignment**: Prospects must be assigned to correct team members
3. **Data Integrity**: All required fields must be properly mapped
4. **Processing Speed**: Records should appear in Bonzo within acceptable timeframe
5. **Error Handling**: Invalid records should be handled gracefully

### Validation Assertions
```python
def test_user_assignment_accuracy():
    """Validate that lo_email correctly resolves to assigned_user"""
    assert prospect.assigned_user.email == sent_payload.lo_email
    assert prospect.assigned_user.id == expected_user_id

def test_data_mapping_integrity():
    """Validate that all required fields are properly mapped"""
    assert prospect.source == "monitorbase"
    assert prospect.first_name == sent_payload.first_name
    assert prospect.email == sent_payload.email

def test_processing_performance():
    """Validate that records are processed within acceptable timeframe"""
    processing_time = prospect.created_at - webhook_sent_time
    assert processing_time.seconds < 60  # Max 60 seconds
```

## Error Handling and Recovery

### Test Failure Scenarios
- Webhook endpoint unavailability
- Invalid payload rejection
- API authentication failures
- Data processing delays
- Missing prospect records

### Recovery Mechanisms
- Automatic retry logic for transient failures
- Graceful degradation for partial failures
- Comprehensive error logging and reporting
- Test data cleanup on failure

## Future Enhancements

### Multi-Integration Support
- Template-based test generation for any integration
- Reusable test components across integrations
- Integration-specific validation rules

### Advanced Testing Features
- Load testing with concurrent webhook delivery
- Stress testing with high-volume payloads
- Performance regression testing
- Automated test scheduling and monitoring

### Integration with CI/CD
- Automated test execution on deployment
- Integration health monitoring alerts
- Performance baseline tracking
- Regression detection and notification