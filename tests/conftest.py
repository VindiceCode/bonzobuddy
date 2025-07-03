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


def pytest_configure(config):
    """Configure pytest markers."""
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