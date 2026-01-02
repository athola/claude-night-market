---
name: development-workflow
description: detailed development workflow covering git, code review, testing, documentation, and deployment practices
version: 1.0.0
created_by: abstract-examples
tags: [development, workflow, git, testing, documentation, deployment]
category: workflow
type: detailed
estimated_tokens: 850
dependencies: []
companion_skills: []
modules:
  - git-workflow
  - code-review
  - testing-strategies
  - documentation-guidelines
  - deployment-procedures
tools:
  - setup-validator
  - workflow-checker
  - quality-metrics
---

# Development Workflow

This is a detailed skill that covers the complete software development workflow from initial setup to deployment. This monolithic approach demonstrates the challenges of large skills and serves as a candidate for modularization.

## Git Workflow Setup

### Repository Initialization

Always start with proper repository initialization:

```bash
# Initialize repository with proper structure
git init
echo "# Project Name" > README.md
git add README.md
git commit -m "Initial commit"

# Set up proper branching strategy
git checkout -b develop
git checkout -b feature/your-feature-name
```

### Branching Strategy

Follow GitFlow or GitHub Flow depending on your team size:

**GitFlow (for teams):**
- `main`: Production releases
- `develop`: Integration branch
- `feature/*`: Feature development
- `release/*`: Release preparation
- `hotfix/*`: Emergency fixes

**GitHub Flow (for small teams):**
- `main`: Always deployable
- `feature/*`: Feature development
- Direct merge to main after review

### Commit Message Standards

Use conventional commits:

```
type(scope): description

feat(api): add user authentication
fix(ui): resolve button styling issue
docs(readme): update installation instructions
test(auth): add unit tests for login function
```

### Daily Git Workflow

1. **Start of day:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/new-work
   ```

2. **During development:**
   ```bash
   # Commit frequently with descriptive messages
   git add .
   git commit -m "feat(component): implement core functionality"

   # Push regularly for backup and collaboration
   git push origin feature/new-work
   ```

3. **End of day:**
   ```bash
   # validate everything is committed and pushed
   git status
   git push origin feature/new-work
   ```

## Code Review Process

### Pull Request Preparation

Before creating a PR:

1. **Self-review your changes:**
   ```bash
   git diff main...feature-branch
   ```

2. **Run all tests:**
   ```bash
   npm test
   # or
   python -m pytest
   # or
   make test
   ```

3. **Check code formatting:**
   ```bash
   make format
   make lint
   ```

### Pull Request Template

Use this PR template:

```markdown
## Description
Brief description of changes and their purpose.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Cross-browser testing (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Guidelines

**For Reviewers:**
1. **Check functionality**: Does the code work as intended?
2. **Review code quality**: Is it readable, maintainable, and follows best practices?
3. **Verify tests**: Are tests detailed and meaningful?
4. **Documentation**: Is documentation updated and accurate?

**For Authors:**
1. **Respond to all feedback**: Address every comment, even if just to acknowledge.
2. **Explain your reasoning**: Help reviewers understand your approach.
3. **Iterate quickly**: Make requested changes promptly.

## Testing Strategies

### Test Pyramid

Follow the testing pyramid:

```
    E2E Tests (10%)
   ─────────────────
  Integration Tests (20%)
 ─────────────────────────
Unit Tests (70%)
```

### Unit Testing

**Best Practices:**
- Test single behavior per test
- Use descriptive test names
- Use AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

**Example (Python/pytest):**
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

### Integration Testing

Test component interactions:

```python
def test_user_registration_flow():
    # Test database, email service, and auth service integration
    with TestClient() as client:
        response = client.post("/register", json={
            "email": "test@example.com",
            "password": "secure_password"
        })
        assert response.status_code == 201
        assert "user_id" in response.json()
```

### End-to-End Testing

Test complete user workflows:

```javascript
// Cypress example
describe('User Checkout Flow', () => {
  it('should complete purchase successfully', () => {
    cy.visit('/products')
    cy.get('[data-cy=product-1]').click()
    cy.get('[data-cy=add-to-cart]').click()
    cy.get('[data-cy=cart]').click()
    cy.get('[data-cy=checkout]').click()
    cy.get('[data-cy=payment-info]').type('4242424242424242')
    cy.get('[data-cy=submit-payment]').click()
    cy.get('[data-cy=order-confirmation]').should('be.visible')
  })
})
```

### Test Data Management

**Use factories:**
```python
# Factory pattern for test data
class UserFactory:
    @staticmethod
    def create(**overrides):
        defaults = {
            "email": "test@example.com",
            "name": "Test User",
            "is_active": True
        }
        return User(**{**defaults, **overrides})
```

**Clean up test data:**
```python
@pytest.fixture
def cleanup_database():
    yield
    # Cleanup after test
    Database.session().query(User).delete()
    Database.session().commit()
```

## Documentation Guidelines

### Code Documentation

**Function documentation:**
```python
def calculate_user_metrics(user_id: int, date_range: DateRange) -> UserMetrics:
    """
    Calculate detailed metrics for a user within the specified date range.

    Args:
        user_id: Unique identifier for the user
        date_range: Start and end dates for metric calculation

    Returns:
        UserMetrics object containing engagement, performance, and activity metrics

    Raises:
        UserNotFoundError: If user_id doesn't exist
        InvalidDateRangeError: If date_range is invalid

    Example:
        >>> metrics = calculate_user_metrics(123, DateRange('2024-01-01', '2024-01-31'))
        >>> print(metrics.total_sessions)
        42
    """
```

**Class documentation:**
```python
class AuthenticationService:
    """
    Handles user authentication, session management, and security.

    This service provides secure authentication mechanisms including
    password-based login, token-based authentication, and session management.
    All operations are logged for security auditing.
    """
```

### API Documentation

**Endpoint documentation:**
```yaml
# OpenAPI 3.0 specification
/users:
  post:
    summary: Create a new user
    description: Creates a new user account with email verification
    tags:
      - Users
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/CreateUserRequest'
    responses:
      201:
        description: User created successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserResponse'
      400:
        description: Invalid input data
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
```

### README Structure

```markdown
# Project Name

## Quick Start
Installation and basic usage in 5 minutes or less.

## Features
Key features and capabilities.

## Installation
Step-by-step installation instructions.

## Usage
Examples and common use cases.

## API Reference
Detailed API documentation.

## Contributing
Development setup and contribution guidelines.

## License
License information.
```

### Changelog Maintenance

**Keep a changelog:**
```markdown
# Changelog

## [1.2.0] - 2024-01-15
### Added
- User authentication system
- Email notification templates

### Changed
- Improved API response times by 40%
- Updated database schema for better performance

### Fixed
- Memory leak in background processing
- Login redirect loop issue

### Security
- Updated dependencies for security patches
- Added rate limiting to API endpoints
```

## Deployment Procedures

### Environment Setup

**Development environment:**
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Manual setup
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
npm install
npm run dev
```

**Production environment:**
```bash
# Production Docker setup
docker-compose -f docker-compose.prod.yml up -d

# Environment variables
export DATABASE_URL=postgresql://user:pass@prod-db:5432/app
export REDIS_URL=redis://prod-redis:6379
export JWT_SECRET=${JWT_SECRET}
```

### Deployment Pipeline

**CI/CD Pipeline (GitHub Actions):**
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: make test
      - name: Run security scan
        run: make security

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deployment commands
          ssh $DEPLOY_SERVER "cd /app && git pull && docker-compose up -d"
```

### Database Migrations

**Safe migration process:**
1. **Backup database:**
   ```bash
   pg_dump production_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run migrations in stages:**
   ```bash
   # Phase 1: Add new columns (nullable)
   alembic upgrade 001_add_new_columns.py

   # Phase 2: Backfill data (in batches)
   python scripts/backfill_new_columns.py

   # Phase 3: Update application code
   # Deploy application code

   # Phase 4: Make changes required
   alembic upgrade 002_make_columns_required.py
   ```

### Monitoring and Alerting

**Health checks:**
```python
@app.route('/health')
def health_check():
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'external_api': check_external_api()
    }

    if all(checks.values()):
        return {'status': 'healthy', 'checks': checks}
    else:
        return {'status': 'unhealthy', 'checks': checks}, 503
```

**Monitoring setup:**
```yaml
# Prometheus configuration
scrape_configs:
  - job_name: 'webapp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Rollback Procedures

**Database rollback:**
```bash
# Identify rollback version
alembic history
alembic downgrade previous_version
```

**Application rollback:**
```bash
# Docker-based rollback
docker-compose down
docker-compose pull previous_tag
docker-compose up -d

# Git-based rollback
git revert HEAD
git push origin main
```

## Quality Metrics

### Code Quality Checks

**Pre-commit hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

**Quality gates:**
```bash
# Makefile
quality-checks:
    black --check .
    isort --check-only .
    flake8 .
    mypy .
    bandit -r .
    safety check
```

### Performance Metrics

**Load testing:**
```python
# Using Locust
class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.client.post("/login", json={"user": "test", "pass": "test"})

    @task
    def view_dashboard(self):
        self.client.get("/dashboard")

    @task(3)
    def view_profile(self):
        self.client.get("/profile")
```

**Performance monitoring:**
```python
# Custom metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware
def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(duration)

    return response
```

## Integration Patterns

### Service Integration

**API integration pattern:**
```python
class ExternalAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def get_data(self, endpoint: str) -> dict:
        response = self.session.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    def post_data(self, endpoint: str, data: dict) -> dict:
        response = self.session.post(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
```

### Database Integration

**Repository pattern:**
```python
class UserRepository:
    def __init__(self, db_session):
        self.db = db_session

    def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def find_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
```

## Error Handling

### Exception Hierarchy

```python
class ApplicationError(Exception):
    """Base application exception"""
    pass

class ValidationError(ApplicationError):
    """Raised when input validation fails"""
    pass

class AuthenticationError(ApplicationError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(ApplicationError):
    """Raised when user lacks permission"""
    pass

class NotFoundError(ApplicationError):
    """Raised when resource is not found"""
    pass
```

### Error Handling Patterns

**Result pattern:**
```python
from typing import Union, Generic, TypeVar
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

@dataclass
class Result(Generic[T, E]):
    value: Optional[T] = None
    error: Optional[E] = None

    @property
    def is_success(self) -> bool:
        return self.error is None

    @property
    def is_failure(self) -> bool:
        return self.error is not None

    @classmethod
    def success(cls, value: T) -> 'Result[T, None]':
        return cls(value=value, error=None)

    @classmethod
    def failure(cls, error: E) -> 'Result[None, E]':
        return cls(value=None, error=error)

# Usage
def authenticate_user(email: str, password: str) -> Result[User, AuthenticationError]:
    try:
        user = User.authenticate(email, password)
        return Result.success(user)
    except AuthenticationError as e:
        return Result.failure(e)
```

This monolithic skill demonstrates several challenges:
1. **Large token usage** (~850+ tokens)
2. **Mixed concerns** (git, testing, deployment, etc.)
3. **Difficult to maintain** (single large file)
4. **Poor reusability** (can't use individual sections)
5. **Hard to test** (complex interactions)

This skill is a perfect candidate for modularization using the patterns demonstrated in the modular-skills framework.
