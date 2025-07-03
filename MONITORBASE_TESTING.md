# Monitorbase Integration Testing

## Purpose

Test that your Monitorbase integration correctly resolves `lo_email` → `user_id` and assigns prospects to the right users.

## Quick Test Commands

```bash
# Test your Monitorbase integration
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v --processing-delay=5

# View detailed results with API calls
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v -s --log-cli-level=INFO

# Generate HTML report
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --html=reports/monitorbase_test.html -v

# Test with fewer records for faster feedback
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --test-records=9 -v
```

## Configuration

Edit `tests/configs/monitorbase_test_config.yaml`:

```yaml
webhook_url: "https://your-middleware-endpoint.com/webhook"  # Your integration endpoint
superuser_api_key: "your_superuser_api_key_here"
test_records: 21
processing_delay: 5

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

## What the Test Does

### 1. Sends Monitorbase Payloads

Sends 21 payloads (7 per user) to your `webhook_url`:

```json
{
  "source": "Monitorbase",
  "lo_email": "escuderi@revolutionmortgage.com",  ← Must resolve to user_id
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
  "tags": ["monitorbase", "inquiry"]
  // ... full Monitorbase payload
}
```

### 2. Validates via Bonzo API

Queries Bonzo using superuser API with `On-Behalf-Of` headers:

```bash
GET /api/v3/prospects
Authorization: Bearer {SUPERUSER_API_KEY}
On-Behalf-Of: 65013  # Queries as each user
```

Searches for prospects with `TestRecord` in the name to verify creation and assignment.

## Expected Results

### Success Log
```
INFO Webhook delivery: 21/21 successful (100.0%)
INFO Making GET request to /api/v3/prospects
INFO Using On-Behalf-Of: 65013
INFO Found 7 test prospects matching 'TestRecord' for user 65013
INFO Found 7/7 test prospects for escuderi@revolutionmortgage.com
INFO Prospect creation: 21/21 prospects found (100.0%)
PASSED
```

### Success Metrics
- **Webhook Delivery**: 95%+ acceptance rate (200 responses)
- **Prospect Creation**: 90%+ prospects created in Bonzo
- **Assignment Accuracy**: 95%+ assigned to correct users
- **API Validation**: Successful `On-Behalf-Of` queries

## Viewing Results

### Console Output
```bash
# Watch webhook delivery and API validation in real-time
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v -s --log-cli-level=INFO
```

**Key metrics to watch**:
- `Webhook delivery: X/Y successful (Z.Z%)`
- `Using On-Behalf-Of: {user_id}`
- `Found X test prospects matching 'TestRecord'`
- `Prospect creation: X/Y prospects found (Z.Z%)`

### HTML Report
```bash
# Generate detailed HTML report
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --html=reports/monitorbase_test.html --self-contained-html -v

# Open report
open reports/monitorbase_test.html
```

### Manual Verification
Check Bonzo dashboard for prospects named `TestRecord_MonitorBase_001`, etc., assigned to correct users.

## Common Issues

### Webhook Failures
```
❌ Webhook delivery: 0/21 successful (0.0%)
```
- Check `webhook_url` is correct and reachable
- Verify endpoint accepts POST requests with JSON
- Check endpoint logs for errors

### No Prospects Found
```
❌ Prospect creation: 0/21 prospects found (0.0%)
```
- Increase `--processing-delay=15` 
- Check if webhooks are creating prospects in Bonzo
- Verify `lo_email` → `user_id` resolution is working

### Assignment Errors
```
❌ Assignment accuracy: 15/21 correct (71.4%)
```
- Check `lo_email` → `user_id` mapping logic
- Verify user_id values in config match Bonzo
- Review prospect assignment in Bonzo dashboard

## Development Workflow

```bash
# 1. Test with dry run first
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --dry-run -v

# 2. Test with small batch
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --test-records=3 --processing-delay=5 -v

# 3. Full test when ready
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v

# 4. Generate report
uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --html=reports/final_test.html -v
```

## What This Validates

✅ **Monitorbase Payload Parsing**: Your endpoint accepts complex Monitorbase payloads  
✅ **lo_email Resolution**: `lo_email` correctly resolves to `user_id`  
✅ **Prospect Creation**: Prospects are created in Bonzo  
✅ **Assignment Logic**: Prospects assigned to correct users based on resolved `user_id`  
✅ **End-to-End Flow**: Complete integration from webhook to prospect assignment

Success means your Monitorbase integration is working correctly and prospects will be assigned to the right loan officers.