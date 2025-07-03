# Monitorbase Integration Testing with Pytest

## Overview

This pytest framework validates Monitorbase integration health by testing that `lo_email` correctly resolves to `user_id` and prospects are properly assigned to the correct users and teams in Bonzo Buddy.

## Core Testing Objective

**Primary Goal**: Validate that when Monitorbase webhooks are sent to our integration endpoint, the `lo_email` field correctly resolves to the appropriate `user_id` and the prospect is assigned to the correct user.

**Control Test**: Send webhooks with explicit `user_id` to verify our superuser middleware works correctly when the field is provided.

## Test Configuration

### Environment Setup

Set these variables in your test configuration:

- `{TEST_HOOK_URL}`: Your main webhook endpoint for Monitorbase integration
- `{SUPERUSER_API_KEY}`: API key with superuser permissions for validation
- `superuser_webhook_url`: Control webhook endpoint that accepts `user_id` field

### Test Users

We test with 3 users across different teams:

| Name | Email | User ID | Team ID |
|------|-------|---------|---------|
| RevTeamUser1 | escuderi@revolutionmortgage.com | 65013 | 12779 |
| RevTeamUser2 | emorgan@revolutionmortgage.com | 27227 | 12211 |
| RevTeamUser3 | mrocco@revolutionmortgage.com | 29194 | 12896 |

## Test Execution

### Basic Integration Test (Primary)

Tests the main Monitorbase integration flow:

```bash
# Run main integration test - validates lo_email → user_id resolution
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v

# Test with 21 records (7 per user)
uv run python -m pytest tests/integration_tests/ --test-records=21 -v
```

### Control Test (Superuser Webhook)

Tests that our middleware works when `user_id` is explicitly provided:

```bash
# Run control test - validates superuser webhook with explicit user_id
uv run python -m pytest tests/integration_tests/ -m superuser -v
```

### Complete Test Suite

```bash
# Run both primary and control tests
uv run python -m pytest tests/integration_tests/ -v --html=reports/monitorbase_integration_report.html
```

## Test Flow

### 1. Webhook Delivery (Primary Test)

**Payload Format** (sent to `{TEST_HOOK_URL}`):
```json
{
  "source": "Monitorbase",
  "lo_email": "escuderi@revolutionmortgage.com",
  "lo_name": "Loan Officer",
  "first_name": "TestRecord_MonitorBase_001",
  "last_name": "Test",
  "email": "test.monitorbase.001@bonzobuddy.test",
  "phone": "555-000-0001",
  // ... other fields
}
```

**What it tests**: Does `lo_email` correctly resolve to the right `user_id`?

### 2. Control Test (Superuser Webhook)

**Payload Format** (sent to `superuser_webhook_url`):
```json
{
  "source": "Monitorbase",
  "user_id": "65013",
  "lo_email": "escuderi@revolutionmortgage.com",
  "first_name": "TestRecord_MonitorBase_SU_001",
  // ... same fields as above
}
```

**What it tests**: Does explicit `user_id` correctly assign prospects (validates middleware)?

### 3. Validation via Superuser API

After webhook delivery, the test queries Bonzo using the superuser API:

```python
# Query prospects for each user using On-Behalf-Of header
headers = {
    'On-Behalf-Of': "{user_id}",
    'Accept': "application/json", 
    'Authorization': "Bearer {SUPERUSER_API_KEY}"
}

response = requests.get("https://app.getbonzo.com/api/v3/prospects", headers=headers)
```

**Validates**:
- Test record exists in Bonzo
- `assigned_user.email` matches the `lo_email` from webhook
- `assigned_user.id` matches expected `user_id`
- `business_entity_id` matches expected `team_id`

## Key Test Commands

### Dry Run (No Actual Webhooks)
```bash
# Test payload generation without sending webhooks
uv run python -m pytest tests/integration_tests/ --dry-run -v
```

### Custom Record Count
```bash
# Test with different record counts
uv run python -m pytest tests/integration_tests/ --test-records=15 -v  # 5 per user
uv run python -m pytest tests/integration_tests/ --test-records=30 -v  # 10 per user
```

### Specific Test Types
```bash
# Run only webhook delivery tests
uv run python -m pytest tests/integration_tests/ -k "webhook_delivery" -v

# Run only prospect validation tests  
uv run python -m pytest tests/integration_tests/ -k "prospect_creation" -v

# Run only assignment accuracy tests
uv run python -m pytest tests/integration_tests/ -k "assignment_accuracy" -v
```

### Processing Delay Configuration
```bash
# Wait longer for webhook processing (default: 30 seconds)
uv run python -m pytest tests/integration_tests/ --processing-delay=60 -v
```

## Test Data Pattern

### Identifiable Test Records
- **Names**: `TestRecord_MonitorBase_001`, `TestRecord_MonitorBase_002`, etc.
- **Emails**: `test.monitorbase.001@bonzobuddy.test`
- **Control Test Names**: `TestRecord_MonitorBase_SU_001` (SU = Superuser)

### Distribution
- 21 total records (default)
- 7 records per user (even distribution)
- Each record has different test user's email as `lo_email`

## Expected Results

### Successful Integration
```json
{
  "assigned_user": {
    "id": 65013,
    "name": "RevTeamUser1", 
    "email": "escuderi@revolutionmortgage.com"
  },
  "business_entity_id": 12779,
  "source": "monitorbase"
}
```

### Test Validation
- ✅ `lo_email` from webhook matches `assigned_user.email` in Bonzo
- ✅ Expected `user_id` matches `assigned_user.id` in Bonzo  
- ✅ Expected `team_id` matches `business_entity_id` in Bonzo
- ✅ Test records appear in correct user's prospect list

## Troubleshooting

### Common Issues

**No prospects found**:
```bash
# Check webhook endpoint is reachable
uv run python -m pytest tests/integration_tests/test_monitorbase_integration.py::TestMonitorbaseIntegration::test_webhook_endpoint_availability -v

# Increase processing delay
uv run python -m pytest tests/integration_tests/ --processing-delay=60 -v
```

**Assignment errors**:
```bash
# Run control test to verify middleware
uv run python -m pytest tests/integration_tests/ -m superuser -v

# Check specific user assignment
uv run python -m pytest tests/integration_tests/test_monitorbase_integration.py::TestMonitorbaseIntegration::test_user_assignment_accuracy -v
```

### Debug Mode
```bash
# Verbose output with detailed logs
uv run python -m pytest tests/integration_tests/ -v -s --tb=long

# Debug specific test
uv run python -m pytest tests/integration_tests/test_monitorbase_integration.py::TestMonitorbaseIntegration::test_bulk_webhook_delivery -v -s
```

## Configuration File

Update `tests/configs/monitorbase_test_config.yaml`:

```yaml
test_name: "Monitorbase Integration Test"
webhook_url: "{TEST_HOOK_URL}"                    # Main integration endpoint
superuser_webhook_url: "{SUPERUSER_WEBHOOK_URL}"  # Control test endpoint  
superuser_api_key: "{SUPERUSER_API_KEY}"
integration_type: "monitorbase"
test_records: 21
distribution: "even"
processing_delay: 30

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
```

## Success Criteria

### Primary Integration Test
- 95%+ webhook delivery success rate
- 90%+ prospect creation rate  
- 95%+ user assignment accuracy
- `lo_email` correctly resolves to `user_id` in all test cases

### Control Test  
- Explicit `user_id` results in correct prospect assignment
- Validates that superuser middleware works when field is provided
- Confirms integration logic is functioning properly

The framework provides comprehensive validation that Monitorbase integration correctly handles `lo_email` → `user_id` resolution and prospect assignment across different teams.