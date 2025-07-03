# Monitorbase Integration Testing Framework

## Overview

This pytest framework validates that your Monitorbase integration correctly resolves `lo_email` to `user_id` and assigns prospects to the right users. It includes both a **real integration test** and a **control test** to ensure your middleware works properly.

## The Two Test Types

### 🎯 **Real Integration Test** (Coming Soon)
Tests your actual Monitorbase integration middleware:
- **Sends to**: `webhook_url` (your middleware endpoint)
- **Payload**: Complex Monitorbase-specific format with `lo_email`
- **Tests**: Does your middleware correctly parse, map, and resolve `lo_email` → `user_id`?

### ✅ **Control Test** (Working Now)
Validates your superuser webhook works when `user_id` is explicit:
- **Sends to**: `superuser_webhook_url` (your control endpoint)
- **Payload**: Simple prospect format with explicit `user_id`
- **Tests**: Does your superuser middleware correctly assign prospects when `user_id` is provided?

## Quick Setup

### 1. Configure Test Settings

Edit `tests/configs/monitorbase_test_config.yaml`:

```yaml
# Webhook endpoints
webhook_url: "https://your-middleware-endpoint.com/webhook"        # Your integration (coming soon)
superuser_webhook_url: "https://your-superuser-endpoint.com/webhook"  # Your control endpoint

# API access
superuser_api_key: "your_superuser_api_key_here"

# Test configuration
test_records: 21
processing_delay: 5  # seconds to wait before API validation

# Test users (your actual users)
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

### 2. Run the Control Test

```bash
# Test that your control webhook + API validation works
uv run python -m pytest tests/integration_tests/ -m superuser -v --processing-delay=5
```

## How the Control Test Works

### Step 1: Send Simple Prospect Payloads

The control test sends **21 simple prospect payloads** (7 per user) to your `superuser_webhook_url`:

```json
{
  "first_name": "TestRecord_001",
  "last_name": "Test",
  "phone": "555-520-4161",
  "email": "test.monitorbase.001@bonzobuddy.test",
  "user_id": "65013"  ← Explicit user_id provided
}
```

**What this tests**: Does your superuser middleware correctly create prospects and assign them when `user_id` is explicitly provided?

### Step 2: Wait for Processing

Waits 5 seconds (configurable) for your webhook to process the prospects.

### Step 3: API Validation

Queries the Bonzo API using your superuser key with `On-Behalf-Of` headers:

```bash
GET https://app.getbonzo.com/api/v3/prospects
Headers:
  Authorization: Bearer {SUPERUSER_API_KEY}
  On-Behalf-Of: 65013  ← Queries as specific user
```

**What this validates**:
- ✅ Prospects were created in Bonzo
- ✅ Each user has the expected number of prospects (7 each)
- ✅ Prospects are assigned to the correct user based on `user_id`
- ✅ Your superuser API integration works

### Expected Control Test Results

```
✅ Webhook delivery: 21/21 successful (100.0%)
✅ API queries: Using On-Behalf-Of headers for each user
✅ Prospect creation: 21/21 prospects found (100.0%)
✅ Assignment accuracy: 7 prospects per user
```

## How the Real Integration Test Will Work (Coming Soon)

### Step 1: Send Monitorbase Payloads

Will send **complex Monitorbase payloads** to your `webhook_url`:

```json
{
  "source": "Monitorbase",
  "lo_email": "escuderi@revolutionmortgage.com",  ← No user_id - must be resolved
  "lo_name": "Loan Officer",
  "first_name": "TestRecord_MonitorBase_001",
  "last_name": "Test",
  "email": "test.monitorbase.001@bonzobuddy.test",
  "phone": "555-000-0001",
  "address": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip": "12345",
  "alert_intel": "Credit Inquiry",
  "alert_date": "2024-01-01",
  "tags": ["monitorbase", "inquiry"],
  // ... many more Monitorbase-specific fields
}
```

**What this will test**: Does your middleware correctly:
1. Parse the complex Monitorbase payload
2. Extract the `lo_email` field  
3. Resolve `lo_email` → `user_id` using your business logic
4. Create prospects assigned to the correct user

### Step 2: Same API Validation

Uses the **exact same API validation** as the control test:
- Queries with `On-Behalf-Of: {user_id}` headers
- Searches for prospects with `TestRecord` pattern
- Validates assignment accuracy

## Key Commands

### Control Test (Works Now)
```bash
# Run control test only
uv run python -m pytest tests/integration_tests/ -m superuser -v

# Control test with custom delay
uv run python -m pytest tests/integration_tests/ -m superuser --processing-delay=10 -v

# Control test with detailed logging
uv run python -m pytest tests/integration_tests/ -m superuser -v -s --log-cli-level=INFO
```

### Real Integration Test (Coming Soon)
```bash
# Run main integration test only  
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v

# Run both tests
uv run python -m pytest tests/integration_tests/ -v
```

### Development Commands
```bash
# Dry run (no actual webhooks)
uv run python -m pytest tests/integration_tests/ --dry-run -v

# Generate HTML report
uv run python -m pytest tests/integration_tests/ --html=reports/integration_report.html -v

# Custom record count
uv run python -m pytest tests/integration_tests/ --test-records=15 -v
```

## Understanding the Test Logs

### Successful Control Test Log

```
INFO Sending 21 superuser webhook requests with user_id
INFO Webhook 20250703_142539_SU_VAL_001: 200 in 0.25s
...
INFO Superuser webhook delivery: 21/21 successful (100.0%)
INFO Waiting 5s for superuser webhook processing
INFO Validating superuser prospects for user RevTeamUser1 (escuderi@revolutionmortgage.com)
INFO Making GET request to /api/v3/prospects
INFO Using On-Behalf-Of: 65013
INFO Response status: 200
INFO Retrieved 7 prospects for user 65013
INFO Found 7 test prospects matching 'TestRecord' for user 65013
INFO Found 7/7 superuser test prospects for escuderi@revolutionmortgage.com
...
INFO Superuser prospect creation: 21/21 prospects found (100.0%)
PASSED
```

### What Each Step Means

1. **Webhook Delivery**: All 21 payloads accepted by your endpoint (200 responses)
2. **Processing Wait**: Framework waits for your webhook to process prospects
3. **API Validation**: Queries Bonzo API using superuser credentials
4. **On-Behalf-Of**: Each query is made as the specific user to see their prospects
5. **Pattern Matching**: Searches for prospects with `TestRecord` in the name
6. **Assignment Validation**: Confirms each user has expected number of prospects

## The Critical Difference

### Control Test Success = Your Infrastructure Works
- ✅ Superuser webhook processes simple payloads correctly
- ✅ API validation mechanism works  
- ✅ `On-Behalf-Of` queries work
- ✅ Prospect assignment logic works when `user_id` is explicit

### Real Integration Test Success = Your Middleware Works
- ✅ All of the above PLUS:
- ✅ Complex Monitorbase payload parsing
- ✅ `lo_email` → `user_id` resolution logic
- ✅ Field mapping and transformation
- ✅ End-to-end integration health

## Troubleshooting

### Control Test Failures

**No prospects found**:
```bash
# Increase processing delay
uv run python -m pytest tests/integration_tests/ -m superuser --processing-delay=15 -v

# Check if webhooks are reaching your endpoint
# Look for 200 responses in logs
```

**API errors**:
```bash
# Verify superuser API key has correct permissions
# Check that On-Behalf-Of headers work for your users
```

**Assignment errors**:
```bash
# Verify user_id values in test config match actual Bonzo user IDs
# Check that superuser can query prospects for these users
```

### Real Integration Test Failures (When Available)

Will likely fail initially because:
- Middleware endpoint not ready
- `lo_email` → `user_id` mapping not implemented  
- Monitorbase payload parsing not complete

## Success Criteria

### Control Test (Must Pass First)
- 95%+ webhook delivery success rate
- 90%+ prospect creation rate via API validation
- 100% assignment accuracy (prospects assigned to correct users)
- API validation working with `On-Behalf-Of` headers

### Real Integration Test (When Ready)
- Same success criteria as control test
- PLUS: Correct `lo_email` → `user_id` resolution
- PLUS: Proper Monitorbase payload handling

## Next Steps

1. **✅ Verify control test passes** - This validates your infrastructure
2. **🔄 Implement your Monitorbase middleware** - The real integration endpoint
3. **🎯 Run real integration test** - This will validate your `lo_email` logic
4. **🚀 Deploy with confidence** - Both tests passing = integration is solid

The control test proves your foundation works. The real integration test will prove your `lo_email` → `user_id` logic works. Together, they give you complete confidence in your Monitorbase integration.