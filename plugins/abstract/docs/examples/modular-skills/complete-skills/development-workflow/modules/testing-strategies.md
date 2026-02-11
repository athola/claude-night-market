---
name: testing-strategies
description: detailed testing framework including unit tests, integration tests, and end-to-end testing patterns
created_by: abstract-examples
tags: [testing, quality, tdd, unit-tests, integration-tests, e2e]
category: testing
type: module
estimated_tokens: 150
dependencies: []
companion_skills: []
modules: []
tools:
  - test-runner
  - coverage-analyzer
  - performance-benchmark
---

# Testing Strategies

A detailed testing framework that validates code quality, reliability, and maintainability through systematic testing practices.

## Overview

Master testing practices with this detailed framework:

**Quick Start**: Get testing working in 5 minutes
- Write your first unit test with AAA pattern
- Add basic integration tests for database/API
- Set up pytest configuration for your project

**Progressive Learning**: Build testing expertise gradually
1. **Foundation** → Unit tests + basic assertions + test naming
2. **Integration** → Database tests + API tests + mocking
3. **Advanced** → E2E tests + performance testing + CI/CD

**Use Case-Based**: Jump to what you need right now
- New project? → Start with unit testing patterns + test structure
- Legacy code? → Use integration tests + mocking strategies
- Production issues? → Apply E2E testing + performance benchmarks
- Team workflow? → Implement CI/CD testing + coverage requirements

## Testing Pyramid

```
    E2E Tests (10%)
   ─────────────────
  Integration Tests (20%)
 ─────────────────────────
Unit Tests (70%)
```

### Unit Tests (Foundation)
- Test individual functions and methods
- Fast execution and isolation
- Mock external dependencies
- High coverage requirements

### Integration Tests (Middleware)
- Test component interactions
- Database and API integrations
- Service layer validations
- Medium execution time

### End-to-End Tests (Surface)
- Test complete user workflows
- Browser automation
- API endpoint testing
- Slowest execution time

## Unit Testing Best Practices

### Test Structure (AAA Pattern)
```python
def test_user_authentication_with_valid_credentials():
    # Arrange
    user = User(email="test@example.com", password="valid_password")
    auth_service = AuthenticationService()

    # Act
    result = auth_service.authenticate(user.email, user.password)

    # Assert
    assert result.is_success
    assert result.user_id == user.id
    assert result.token is not None
```

### Test Naming Conventions
```python
# Good: Descriptive and specific
def test_user_registration_with_duplicate_email_raises_error()
def test_password_reset_token_expires_after_24_hours()

# Bad: Vague and generic
def test_user_registration()
def test_password_reset()
```

### Test Organization
```python
class TestUserAuthentication:
    def test_valid_credentials_return_success(self):
        """Test successful authentication with valid credentials"""
        pass

    def test_invalid_password_returns_failure(self):
        """Test authentication fails with wrong password"""
        pass

    def test_nonexistent_user_returns_failure(self):
        """Test authentication fails for unknown user"""
        pass

class TestUserRegistration:
    def test_valid_registration_creates_user(self):
        """Test user creation with valid data"""
        pass

    def test_duplicate_email_raises_validation_error(self):
        """Test registration fails with duplicate email"""
        pass
```

### Mocking External Dependencies
```python
from unittest.mock import Mock, patch
import pytest

class TestUserService:
    @patch('services.email_service.EmailService.send_welcome_email')
    def test_user_registration_sends_welcome_email(self, mock_email):
        # Arrange
        mock_email.return_value = True
        user_data = {"email": "test@example.com", "name": "Test User"}
        user_service = UserService()

        # Act
        user = user_service.create_user(user_data)

        # Assert
        mock_email.assert_called_once_with(user_data["email"], user_data["name"])
        assert user.email == user_data["email"]
```

## Integration Testing

### Database Integration Tests
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_repository_integration(test_db):
    # Arrange
    user_repo = UserRepository(test_db)
    user_data = {"email": "test@example.com", "name": "Test User"}

    # Act
    user = user_repo.create(user_data)
    found_user = user_repo.find_by_id(user.id)

    # Assert
    assert found_user.email == user_data["email"]
    assert found_user.name == user_data["name"]
```

### API Integration Tests
```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_user_registration_flow(client):
    # Test complete registration flow
    response = client.post("/register", json={
        "email": "test@example.com",
        "password": "secure_password",
        "name": "Test User"
    })

    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "test@example.com"
    assert "id" in user_data
    assert "token" in user_data
```

### Service Integration Tests
```python
def test_payment_service_integration():
    # Test payment processing with external provider
    payment_service = PaymentService(
        payment_gateway=MockPaymentGateway(),
        notification_service=MockNotificationService()
    )

    result = payment_service.process_payment(
        amount=100.0,
        currency="USD",
        payment_method="credit_card"
    )

    assert result.success
    assert result.transaction_id is not None
    payment_service.notification_service.send.assert_called_once()
```

## End-to-End Testing

### Web Application E2E Tests (Cypress)
```javascript
describe('User E-commerce Journey', () => {
  beforeEach(() => {
    cy.visit('/products')
    cy.clearCookies()
  })

  it('should complete purchase from product to order confirmation', () => {
    // Browse products
    cy.get('[data-cy=product-card]').first().click()
    cy.get('[data-cy=add-to-cart]').click()

    // View cart and checkout
    cy.get('[data-cy=cart-icon]').click()
    cy.get('[data-cy=checkout-button]').click()

    // Enter shipping information
    cy.get('[data-cy=shipping-form]').within(() => {
      cy.get('[name=address]').type('123 Main St')
      cy.get('[name=city]').type('Anytown')
      cy.get('[name=zip]').type('12345')
    })

    // Enter payment information
    cy.get('[data-cy=payment-form]').within(() => {
      cy.get('[name=card-number]').type('4242424242424242')
      cy.get('[name=expiry]').type('12/25')
      cy.get('[name=cvv]').type('123')
    })

    // Submit order
    cy.get('[data-cy=submit-order]').click()

    // Verify order confirmation
    cy.get('[data-cy=order-confirmation]').should('be.visible')
    cy.get('[data-cy=order-number]').should('not.be.empty')
  })
})
```

### API E2E Tests
```python
def test_complete_order_workflow_api():
    """Test complete order workflow through API endpoints"""
    with TestClient() as client:
        # 1. User registration
        register_response = client.post("/api/users/register", json={
            "email": "customer@example.com",
            "password": "secure_password",
            "name": "Test Customer"
        })
        user_id = register_response.json()["id"]
        token = register_response.json()["token"]

        # 2. Authentication
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 3. Browse products
        products_response = client.get("/api/products", headers=auth_headers)
        product_id = products_response.json()[0]["id"]

        # 4. Add to cart
        cart_response = client.post("/api/cart/items",
            headers=auth_headers,
            json={"product_id": product_id, "quantity": 2}
        )

        # 5. Create order
        order_response = client.post("/api/orders",
            headers=auth_headers,
            json={
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zip": "12345"
                },
                "payment_method": "credit_card"
            }
        )

        assert order_response.status_code == 201
        order_data = order_response.json()
        assert order_data["status"] == "pending"
        assert len(order_data["items"]) == 1
```

## Test Data Management

### Factory Pattern for Test Data
```python
import factory
from factory import fuzzy
from datetime import datetime, timedelta

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    is_active = True
    created_at = factory.LazyFunction(datetime.now)

class OrderFactory(factory.Factory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = fuzzy.FuzzyChoice(["pending", "processing", "shipped", "delivered"])
    total_amount = factory.LazyAttribute(lambda obj: sum(item.price * item.quantity for item in obj.items))
    created_at = factory.LazyFunction(datetime.now)

class OrderItemFactory(factory.Factory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = fuzzy.FuzzyInteger(1, 5)
    price = factory.LazyAttribute(lambda obj: obj.product.price)
```

### Fixtures and Cleanup
```python
@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    user = UserFactory.create()
    yield user
    user.delete()

@pytest.fixture
def populated_cart():
    """Create a cart with sample items"""
    cart = Cart.create()
    for product in ProductFactory.create_batch(3):
        cart.add_item(product, quantity=2)
    yield cart
    cart.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup and cleanup test database"""
    setup_test_db()
    yield
    cleanup_test_db()
```

## Test Organization and Structure

### Directory Structure
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_utils.py
│   └── fixtures/
│       ├── sample_data.json
│       └── mock_responses.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_external_services.py
├── e2e/
│   ├── test_user_journeys.py
│   ├── test_workflows.py
│   └── test_scenarios.py
├── conftest.py
├── helpers.py
└── requirements-test.txt
```

### Configuration Files
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    external: Tests requiring external services
```

## Performance Testing

### Load Testing with Locust
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts"""
        response = self.client.post("/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_products(self):
        """Browse products page"""
        self.client.get("/products")

    @task(2)
    def view_product_details(self):
        """View individual product"""
        self.client.get("/products/1")

    @task(1)
    def add_to_cart(self):
        """Add item to cart"""
        self.client.post("/cart/items",
            json={"product_id": 1, "quantity": 1},
            headers=getattr(self, 'headers', {})
        )

    @task(1)
    def checkout(self):
        """Complete checkout process"""
        if hasattr(self, 'headers'):
            self.client.post("/orders",
                json={"shipping_address": {}, "payment_method": "credit_card"},
                headers=self.headers
            )
```

### Performance Benchmarks
```python
import time
import statistics
from typing import List

def benchmark_function(func, *args, iterations=100) -> dict:
    """Benchmark a function's performance"""
    times = []

    for _ in range(iterations):
        start_time = time.perf_counter()
        result = func(*args)
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "std_dev": statistics.stdev(times) if len(times) > 1 else 0
    }

def test_search_performance():
    """Test search function performance"""
    results = benchmark_function(search_service.search, "test query")

    assert results["mean"] < 0.1  # Average under 100ms
    assert results["max"] < 0.5   # Maximum under 500ms
    assert results["std_dev"] < 0.05  # Consistent performance
```

## Test Quality and Coverage

### Coverage Requirements
```python
# Test configuration for coverage
def run_tests_with_coverage():
    """Run tests with coverage analysis"""
    cmd = [
        "pytest",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=85"
    ]
    subprocess.run(cmd, check=True)
```

### Test Quality Metrics
```python
def analyze_test_quality(test_files: List[str]) -> dict:
    """Analyze test quality metrics"""
    metrics = {
        "total_tests": 0,
        "test_classes": 0,
        "assertions_per_test": [],
        "test_names_length": [],
        "mock_usage": 0
    }

    for file in test_files:
        # Parse test files and extract metrics
        # Implementation details...
        pass

    return {
        "average_assertions": statistics.mean(metrics["assertions_per_test"]),
        "average_test_name_length": statistics.mean(metrics["test_names_length"]),
        "mock_ratio": metrics["mock_usage"] / metrics["total_tests"]
    }
```

## Continuous Integration Testing

### GitHub Actions Test Workflow
```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run E2E tests
        run: pytest tests/e2e/ -v
        env:
          TEST_ENVIRONMENT: ci

      - name: Generate coverage report
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices Checklist

### Before Writing Tests
- [ ] Understand the requirements and expected behavior
- [ ] Identify edge cases and boundary conditions
- [ ] Plan test scenarios and data requirements
- [ ] Choose appropriate testing framework and tools

### During Test Writing
- [ ] Use descriptive test names that explain what is being tested
- [ ] Follow AAA pattern (Arrange, Act, Assert)
- [ ] Test one behavior per test
- [ ] Use appropriate assertions
- [ ] Mock external dependencies
- [ ] Use test data factories instead of hardcoded values

### Test Maintenance
- [ ] Keep tests independent and isolated
- [ ] Update tests when requirements change
- [ ] Regularly review and refactor tests
- [ ] Monitor test execution times
- [ ] Maintain high coverage without sacrificing readability

This detailed testing strategy validates reliable, maintainable software through systematic quality assurance practices.
