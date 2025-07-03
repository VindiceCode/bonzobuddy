import pytest
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestUser:
    """Test user configuration."""
    name: str
    email: str
    user_id: int
    team_id: int


@dataclass
class ValidationRule:
    """Validation rule configuration."""
    field: str
    expected: str = None
    matches_lo_email: bool = False


@dataclass
class TestConfig:
    """Test configuration loaded from YAML."""
    test_name: str
    webhook_url: str
    superuser_webhook_url: str
    superuser_api_key: str
    integration_type: str
    test_records: int
    distribution: str
    processing_delay: int
    test_users: List[TestUser]
    validation_rules: List[ValidationRule]


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--test-records",
        action="store",
        default=None,
        type=int,
        help="Override number of test records to generate"
    )
    parser.addoption(
        "--processing-delay",
        action="store",
        default=None,
        type=int,
        help="Override processing delay in seconds"
    )
    parser.addoption(
        "--config",
        action="store",
        default="tests/configs/monitorbase_test_config.yaml",
        help="Path to test configuration file"
    )
    parser.addoption(
        "--dry-run",
        action="store_true",
        default=False,
        help="Perform dry run without making actual API calls"
    )
    parser.addoption(
        "--inthelp",
        action="store_true",
        default=False,
        help="Show common integration test patterns and commands"
    )


@pytest.fixture(scope="session")
def test_config(request) -> TestConfig:
    """Load test configuration from YAML file."""
    config_path = request.config.getoption("--config")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Test configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Override with command line options if provided
    if request.config.getoption("--test-records"):
        config_data["test_records"] = request.config.getoption("--test-records")
    
    if request.config.getoption("--processing-delay"):
        config_data["processing_delay"] = request.config.getoption("--processing-delay")
    
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
        superuser_webhook_url=config_data.get("superuser_webhook_url", config_data["webhook_url"]),
        superuser_api_key=config_data["superuser_api_key"],
        integration_type=config_data["integration_type"],
        test_records=config_data["test_records"],
        distribution=config_data["distribution"],
        processing_delay=config_data["processing_delay"],
        test_users=test_users,
        validation_rules=validation_rules
    )


@pytest.fixture(scope="session")
def is_dry_run(request) -> bool:
    """Check if this is a dry run."""
    return request.config.getoption("--dry-run")


@pytest.fixture(scope="session")
def test_run_id() -> str:
    """Generate unique test run ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@pytest.fixture(scope="session")
def test_data_pattern(test_config, test_run_id) -> str:
    """Generate test data naming pattern."""
    return f"TestRecord_{test_config.integration_type.title()}_{test_run_id}"


@pytest.fixture
def payload_template(test_config) -> Dict[str, Any]:
    """Load payload template for the integration."""
    template_path = f"tests/fixtures/{test_config.integration_type}_payload_template.json"
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Payload template not found: {template_path}")
    
    import json
    with open(template_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def superuser_payload_template(test_config) -> Dict[str, Any]:
    """Load superuser payload template for the integration."""
    template_path = f"tests/fixtures/{test_config.integration_type}_superuser_payload_template.json"
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Superuser payload template not found: {template_path}")
    
    import json
    with open(template_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def reports_dir() -> Path:
    """Ensure reports directory exists."""
    reports_path = Path("reports/integration_health_reports")
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path


@pytest.fixture(autouse=True)
def test_environment_check():
    """Verify test environment is properly configured."""
    required_dirs = [
        "tests/configs",
        "tests/fixtures", 
        "scripts",
        "reports"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            raise EnvironmentError(f"Required directory missing: {dir_path}")


def show_integration_help():
    """Display common integration test patterns and commands."""
    help_text = """
🧪 MONITORBASE INTEGRATION TEST PATTERNS

═══════════════════════════════════════════════════════════════════════

📋 CONTROL TESTS (Validate Infrastructure)
    Test your superuser webhook with explicit user_id field

    # Run control test only
    uv run python -m pytest tests/integration_tests/ -m superuser -v

    # Control test with custom delay
    uv run python -m pytest tests/integration_tests/ -m superuser --processing-delay=10 -v

    # Control test with detailed logging
    uv run python -m pytest tests/integration_tests/ -m superuser -v -s --log-cli-level=INFO

═══════════════════════════════════════════════════════════════════════

🎯 REAL INTEGRATION TESTS (Test lo_email → user_id Resolution)
    Test your Monitorbase middleware with lo_email field

    # Run main integration test
    uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v

    # Test with detailed logging and API calls
    uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v -s --log-cli-level=INFO

    # Test with fewer records for faster feedback
    uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --test-records=9 -v

    # Test with longer processing delay
    uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" --processing-delay=15 -v

═══════════════════════════════════════════════════════════════════════

📊 REPORTS & ANALYSIS

    # Generate HTML report
    uv run python -m pytest tests/integration_tests/ --html=reports/test_report.html -v

    # Self-contained HTML report (no external assets)
    uv run python -m pytest tests/integration_tests/ --html=reports/test_report.html --self-contained-html -v

    # Run both control and real tests with report
    uv run python -m pytest tests/integration_tests/ -v --html=reports/full_integration_report.html

═══════════════════════════════════════════════════════════════════════

🔧 DEVELOPMENT & DEBUGGING

    # Dry run (no actual webhooks sent)
    uv run python -m pytest tests/integration_tests/ --dry-run -v

    # Test specific functions
    uv run python -m pytest tests/integration_tests/ -k "webhook_delivery" -v
    uv run python -m pytest tests/integration_tests/ -k "prospect_creation" -v
    uv run python -m pytest tests/integration_tests/ -k "assignment_accuracy" -v

    # Custom record counts
    uv run python -m pytest tests/integration_tests/ --test-records=3 -v   # Quick test
    uv run python -m pytest tests/integration_tests/ --test-records=30 -v  # Stress test

═══════════════════════════════════════════════════════════════════════

⚡ QUICK PATTERNS

    Control Test Only:       uv run python -m pytest tests/integration_tests/ -m superuser -v
    Real Integration Only:   uv run python -m pytest tests/integration_tests/ -m "webhook and not superuser" -v
    Everything:              uv run python -m pytest tests/integration_tests/ -v
    With HTML Report:        uv run python -m pytest tests/integration_tests/ -v --html=reports/test.html
    Fast Feedback:           uv run python -m pytest tests/integration_tests/ -m superuser --test-records=3 -v
    Detailed Logging:        uv run python -m pytest tests/integration_tests/ -m superuser -v -s --log-cli-level=INFO

═══════════════════════════════════════════════════════════════════════

📍 KEY MARKERS

    -m superuser             Control tests (explicit user_id)
    -m "webhook and not superuser"  Real integration tests (lo_email → user_id)
    -m webhook               All webhook delivery tests
    -m api                   All API validation tests
    -m data_integrity        Data mapping validation tests
    -m slow                  Performance/timing tests

═══════════════════════════════════════════════════════════════════════

🎯 SUCCESS CRITERIA

    Control Test Success:    95%+ webhook delivery, 90%+ prospect creation, 100% assignment accuracy
    Real Integration Success: Same as control + correct lo_email → user_id resolution

═══════════════════════════════════════════════════════════════════════
"""
    print(help_text)


def pytest_configure(config):
    """Configure pytest markers."""
    # Show help and exit if --inthelp is used
    if config.getoption("--inthelp"):
        show_integration_help()
        pytest.exit("Integration test help displayed", returncode=0)
    
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "webhook: mark test as webhook delivery test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API validation test"
    )
    config.addinivalue_line(
        "markers", "data_integrity: mark test as data integrity test"
    )
    config.addinivalue_line(
        "markers", "superuser: mark test as superuser webhook test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location."""
    for item in items:
        # Add integration marker to all integration tests
        if "integration_tests" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add specific markers based on test names
        if "webhook" in item.name:
            item.add_marker(pytest.mark.webhook)
        elif "api" in item.name:
            item.add_marker(pytest.mark.api)
        elif "data_integrity" in item.name:
            item.add_marker(pytest.mark.data_integrity)
        elif "superuser" in item.name:
            item.add_marker(pytest.mark.superuser)
        elif "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)