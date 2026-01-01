# Error Handling Tutorial

This tutorial provides practical guidance for implementing robust error handling in Claude Code skills and plugins. It covers real-world scenarios, code examples, and best practices.

## Table of Contents

1. [Understanding Error Types](#understanding-error-types)
2. [Error Classification System](#error-classification-system)
3. [Practical Error Handling Patterns](#practical-error-handling-patterns)
4. [Real-World Examples](#real-world-examples)
5. [Debugging Techniques](#debugging-techniques)
6. [Testing Error Scenarios](#testing-error-scenarios)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

## Understanding Error Types

### 1. System Errors
These are errors caused by the underlying system environment:
- Network failures
- File system issues
- Memory exhaustion
- Database connection problems

### 2. Logic Errors
Errors in the program's logic or flow:
- Invalid input handling
- Incorrect assumptions
- Boundary condition failures
- State inconsistencies

### 3. Integration Errors
Errors when interacting with external services:
- API failures
- Authentication issues
- Rate limiting
- Service unavailability

### 4. User Errors
Errors caused by user actions or input:
- Invalid configuration
- Incorrect usage patterns
- Permission issues
- Resource conflicts

## Error Classification System

Based on the leyline:error-patterns standard:

### Critical Errors (Halt Execution)
```python
# E001-E099: Critical system failures
class CriticalError(Exception):
    """Error that requires immediate halt of execution"""
    pass

class AuthenticationError(CriticalError):
    """Authentication has permanently failed"""
    def __init__(self, service, message="Authentication failed"):
        self.service = service
        self.code = "E001"
        super().__init__(f"[{self.code}] {service}: {message}")
```

### Recoverable Errors (Retry or Fallback)
```python
# E010-E099: Recoverable errors
class RecoverableError(Exception):
    """Error that might be resolved with retry or fallback"""
    pass

class NetworkTimeoutError(RecoverableError):
    """Network operation timed out"""
    def __init__(self, operation, timeout):
        self.operation = operation
        self.timeout = timeout
        self.code = "E010"
        super().__init__(f"[{self.code}] {operation} timed out after {timeout}s")
```

### Warnings (Continue with Logging)
```python
# E020-E099: Warning conditions
class WarningError(Exception):
    """Warning condition that should be logged but doesn't halt execution"""
    pass

class PerformanceWarning(WarningError):
    """Operation is slower than expected"""
    def __init__(self, operation, duration, threshold):
        self.operation = operation
        self.duration = duration
        self.threshold = threshold
        self.code = "E020"
        super().__init__(f"[{self.code}] {operation} took {duration:.2f}s (threshold: {threshold}s)")
```

## Practical Error Handling Patterns

### 1. The Try-Except-Else-Finally Pattern
```python
import logging

logger = logging.getLogger(__name__)

def robust_file_operation(filepath):
    """Pattern for file operations with comprehensive error handling"""
    try:
        # Try to open and process file
        with open(filepath, 'r') as f:
            data = f.read()

    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"E002 File not found: {filepath}")

    except PermissionError:
        logger.error(f"Permission denied: {filepath}")
        raise PermissionError(f"E006 Permission denied: {filepath}")

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in {filepath}: {e}")
        # Try alternative encoding
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = f.read()
            logger.warning(f"Used alternative encoding for {filepath}")
        except Exception:
            raise ValueError(f"E012 Cannot decode file: {filepath}")

    else:
        # File opened successfully
        logger.info(f"Successfully read {filepath}")
        return data

    finally:
        # Cleanup (if needed)
        pass
```

### 2. Retry with Exponential Backoff
```python
import time
import random
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Any:
    """
    Execute operation with exponential backoff retry logic
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await operation()

        except (ConnectionError, TimeoutError) as e:
            last_exception = e

            if attempt == max_retries:
                break

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (0.5 + random.random() * 0.5)

            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
            )
            await asyncio.sleep(delay)

        except Exception as e:
            # Don't retry non-transient errors
            logger.error(f"Non-retryable error: {e}")
            raise

    raise last_exception
```

### 3. Circuit Breaker Pattern
```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("E015 Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)

                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0

                return result

            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN

                raise

        return wrapper
```

### 4. Graceful Degradation Pattern
```python
from typing import Optional, Dict, Any

class GracefulDegradation:
    """Implement graceful degradation when services fail"""

    def __init__(self):
        self.fallbacks = {}

    def register_fallback(self, operation: str, fallback_func: Callable):
        """Register a fallback function for an operation"""
        self.fallbacks[operation] = fallback_func

    async def execute(self, operation: str, primary_func: Callable, *args, **kwargs) -> Any:
        """
        Execute primary function with fallback to secondary
        """
        try:
            return await primary_func(*args, **kwargs)

        except Exception as e:
            logger.error(f"Primary operation failed: {e}")

            if operation in self.fallbacks:
                logger.info(f"Using fallback for {operation}")
                try:
                    return await self.fallbacks[operation](*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise Exception(f"E016 Both primary and fallback failed for {operation}")
            else:
                raise

# Usage example
degradation = GracefulDegradation()

# Register fallbacks
degradation.register_fallback(
    "fetch_data",
    lambda: fetch_from_cache()  # Fallback to cache
)

# Execute with fallback
data = await degradation.execute(
    "fetch_data",
    fetch_from_api  # Primary function
)
```

## Real-World Examples

### Example 1: API Client with Relevant Error Handling
```python
import aiohttp
import asyncio
from typing import Optional, Dict, Any

class RobustAPIClient:
    """API client with relevant error handling"""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry_with_backoff(max_retries=3)
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with comprehensive error handling"""

        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                # Handle HTTP status codes
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise AuthenticationError("API", "Invalid credentials")
                elif response.status == 403:
                    raise PermissionError("E006 Access forbidden")
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError("API", retry_after)
                elif response.status >= 500:
                    raise ServerError(f"E017 Server error: {response.status}")
                else:
                    raise APIError(f"E018 Unexpected status: {response.status}")

        except asyncio.TimeoutError:
            raise NetworkTimeoutError(f"{method} {url}", self.timeout.total)

        except aiohttp.ClientError as e:
            raise ConnectionError(f"E019 Connection error: {e}")

        except Exception as e:
            raise APIError(f"E020 Unexpected error: {e}")

# Usage
async def fetch_user_data(user_id: int):
    try:
        async with RobustAPIClient("https://api.example.com") as client:
            return await client.request("GET", f"users/{user_id}")

    except AuthenticationError:
        logger.error("API authentication failed")
        return {"error": "authentication_required"}

    except RateLimitError as e:
        logger.warning(f"Rate limited, retry after {e.retry_after}s")
        return {"error": "rate_limited", "retry_after": e.retry_after}

    except NetworkTimeoutError:
        logger.error("Network timeout")
        return {"error": "timeout"}

    except Exception as e:
        logger.error(f"Failed to fetch user data: {e}")
        return {"error": "unknown"}
```

### Example 2: Data Processing Pipeline
```python
import asyncio
import logging
from typing import List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class DataProcessor:
    """Robust data processing pipeline"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.processed_count = 0
        self.error_count = 0

    async def process_batch(self, items: List[Any]) -> List[ProcessingResult]:
        """Process a batch of items with error isolation"""

        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_isolation(item):
            async with semaphore:
                return await self.process_item(item)

        # Process all items concurrently
        tasks = [process_with_isolation(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        error=f"E021 Processing failed: {str(result)}"
                    )
                )
                self.error_count += 1
            else:
                processed_results.append(result)
                if result.success:
                    self.processed_count += 1
                else:
                    self.error_count += 1

        return processed_results

    async def process_item(self, item: Any) -> ProcessingResult:
        """Process single item with comprehensive error handling"""

        warnings = []

        try:
            # Validate input
            if not self.validate_input(item):
                return ProcessingResult(
                    success=False,
                    error="E022 Invalid input format"
                )

            # Transform data
            try:
                transformed = await self.transform_data(item)
            except TransformationError as e:
                return ProcessingResult(
                    success=False,
                    error=f"E023 Transformation failed: {e}"
                )

            # Validate transformation
            validation_warnings = self.validate_output(transformed)
            warnings.extend(validation_warnings)

            # Store result
            try:
                await self.store_result(transformed)
            except StorageError as e:
                # Try alternative storage
                try:
                    await self.store_alternatively(transformed)
                    warnings.append("W001 Used alternative storage")
                except Exception:
                    return ProcessingResult(
                        success=False,
                        error=f"E024 Storage failed: {e}"
                    )

            return ProcessingResult(
                success=True,
                data=transformed,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Unexpected error processing item: {e}")
            return ProcessingResult(
                success=False,
                error=f"E025 Unexpected error: {e}"
            )

    def validate_input(self, item: Any) -> bool:
        """Validate input data"""
        # Implementation depends on your data structure
        return item is not None

    async def transform_data(self, item: Any) -> Any:
        """Transform data with error handling"""
        # Your transformation logic here
        return item

    def validate_output(self, data: Any) -> List[str]:
        """Validate output and return warnings"""
        warnings = []
        # Your validation logic here
        return warnings

    async def store_result(self, data: Any) -> None:
        """Store result"""
        # Your storage logic here
        pass

    async def store_alternatively(self, data: Any) -> None:
        """Alternative storage method"""
        # Fallback storage logic here
        pass
```

## Debugging Techniques

### 1. Structured Logging
```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """Logger for structured error reporting"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        user_id: str = None,
        request_id: str = None
    ):
        """Log error with structured context"""

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_code": getattr(error, 'code', 'UNKNOWN'),
            "context": context or {},
            "user_id": user_id,
            "request_id": request_id,
            "traceback": traceback.format_exc()
        }

        self.logger.error(json.dumps(error_data))

    def log_warning(
        self,
        message: str,
        context: Dict[str, Any] = None,
        warning_code: str = "W000"
    ):
        """Log warning with context"""

        warning_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "warning_code": warning_code,
            "context": context or {}
        }

        self.logger.warning(json.dumps(warning_data))
```

### 2. Debug Decorator
```python
import functools
import time
import traceback
from typing import Callable, Any

def debug_errors(
    log_args: bool = True,
    log_result: bool = True,
    log_traceback: bool = True
):
    """Decorator for debugging function errors"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                if log_args:
                    logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

                result = await func(*args, **kwargs)

                if log_result:
                    logger.debug(f"{func.__name__} returned: {type(result)}")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                error_info = {
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

                if log_args:
                    error_info["args"] = args
                    error_info["kwargs"] = kwargs

                if log_traceback:
                    error_info["traceback"] = traceback.format_exc()

                logger.error(f"Error in {func.__name__}: {json.dumps(error_info)}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                if log_args:
                    logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

                result = func(*args, **kwargs)

                if log_result:
                    logger.debug(f"{func.__name__} returned: {type(result)}")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                error_info = {
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

                if log_args:
                    error_info["args"] = args
                    error_info["kwargs"] = kwargs

                if log_traceback:
                    error_info["traceback"] = traceback.format_exc()

                logger.error(f"Error in {func.__name__}: {json.dumps(error_info)}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Usage
@debug_errors()
async def problematic_function(data):
    # This function will have comprehensive error logging
    return await process_data(data)
```

## Testing Error Scenarios

### 1. Error Injection Testing
```python
import pytest
from unittest.mock import patch, AsyncMock
from contextlib import asynccontextmanager

class ErrorInjector:
    """Inject errors for testing purposes"""

    def __init__(self):
        self.errors = {}

    def inject_error(self, function_name: str, error: Exception):
        """Inject error for specific function"""
        self.errors[function_name] = error

    def should_error(self, function_name: str) -> bool:
        """Check if function should error"""
        return function_name in self.errors

    def get_error(self, function_name: str) -> Exception:
        """Get injected error"""
        return self.errors[function_name]

# Test example
@pytest.mark.asyncio
async def test_api_client_with_errors():
    injector = ErrorInjector()

    # Test network timeout
    injector.inject_error("request", asyncio.TimeoutError())

    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.side_effect = injector.get_error("request")

        async with RobustAPIClient("https://api.example.com") as client:
            with pytest.raises(NetworkTimeoutError):
                await client.request("GET", "test")

    # Test server error
    injector.errors = {}
    mock_response = AsyncMock()
    mock_response.status = 500

    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value = mock_response

        async with RobustAPIClient("https://api.example.com") as client:
            with pytest.raises(ServerError):
                await client.request("GET", "test")
```

### 2. Property-Based Testing
```python
import hypothesis
from hypothesis import given, strategies as st

@given(st.lists(st.integers(), min_size=1, max_size=100))
def test_sort_with_error_handling(numbers):
    """Test sorting function with various inputs"""

    try:
        result = robust_sort(numbers)
        assert result == sorted(numbers)

    except ValueError as e:
        # Should handle invalid inputs gracefully
        assert "invalid" in str(e).lower()

    except Exception as e:
        # No other exceptions should occur
        pytest.fail(f"Unexpected exception: {e}")
```

## Monitoring and Observability

### 1. Error Metrics Collection
```python
from collections import defaultdict, deque
import time
from typing import Dict, List

class ErrorMetrics:
    """Collect and analyze error metrics"""

    def __init__(self, window_size: int = 3600):  # 1 hour window
        self.window_size = window_size
        self.error_counts = defaultdict(int)
        self.error_history = deque()
        self.recent_errors = deque(maxlen=100)

    def record_error(
        self,
        error_code: str,
        error_type: str,
        context: Dict[str, Any] = None
    ):
        """Record an error occurrence"""

        timestamp = time.time()

        # Update counts
        self.error_counts[error_code] += 1
        self.error_counts[f"{error_type}_{error_code}"] += 1

        # Add to history
        error_record = {
            "timestamp": timestamp,
            "error_code": error_code,
            "error_type": error_type,
            "context": context or {}
        }

        self.error_history.append(error_record)
        self.recent_errors.append(error_record)

        # Clean old records
        cutoff = timestamp - self.window_size
        while self.error_history and self.error_history[0]["timestamp"] < cutoff:
            self.error_history.popleft()

    def get_error_rate(self, duration: float = 300) -> float:
        """Get error rate in the last duration (seconds)"""

        cutoff = time.time() - duration
        recent_errors = [
            e for e in self.error_history
            if e["timestamp"] > cutoff
        ]

        return len(recent_errors) / duration

    def get_top_errors(self, limit: int = 10) -> List[tuple]:
        """Get most frequent errors"""

        return sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def check_error_spike(self, threshold: float = 2.0, window: int = 300) -> bool:
        """Check if error rate has spiked"""

        current_rate = self.get_error_rate(window)
        baseline_rate = self.get_error_rate(window * 2) / 2

        return current_rate > baseline_rate * threshold
```

### 2. Health Check System
```python
from typing import Dict, List, Callable
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    check_func: Callable
    timeout: float = 5.0
    critical: bool = True

class HealthMonitor:
    """Monitor system health"""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.metrics = ErrorMetrics()

    def register_check(self, health_check: HealthCheck):
        """Register a health check"""
        self.checks[health_check.name] = health_check

    async def run_check(self, check_name: str) -> Dict[str, Any]:
        """Run a specific health check"""

        if check_name not in self.checks:
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": f"E026 Unknown health check: {check_name}"
            }

        check = self.checks[check_name]

        try:
            async with asyncio.timeout(check.timeout):
                result = await check.check_func()

            return {
                "status": HealthStatus.HEALTHY,
                "result": result,
                "timestamp": time.time()
            }

        except asyncio.TimeoutError:
            error_code = "E027"
            self.metrics.record_error(error_code, "timeout", {"check": check_name})

            return {
                "status": HealthStatus.UNHEALTHY if check.critical else HealthStatus.DEGRADED,
                "error": f"[{error_code}] Health check timed out",
                "timestamp": time.time()
            }

        except Exception as e:
            error_code = "E028"
            self.metrics.record_error(error_code, "health_check", {
                "check": check_name,
                "error": str(e)
            })

            return {
                "status": HealthStatus.UNHEALTHY if check.critical else HealthStatus.DEGRADED,
                "error": f"[{error_code}] Health check failed: {e}",
                "timestamp": time.time()
            }

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""

        results = {}
        overall_status = HealthStatus.HEALTHY

        for check_name in self.checks:
            result = await self.run_check(check_name)
            results[check_name] = result

            # Update overall status
            if result["status"] == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result["status"] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": time.time(),
            "error_rate": self.metrics.get_error_rate()
        }
```

## Common Pitfalls and Solutions

### Pitfall 1: Swallowing Exceptions
```python
# BAD: Swallowing exceptions without logging
try:
    result = risky_operation()
except:
    pass  # Silent failure!

# GOOD: Proper exception handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise  # Re-raise or handle appropriately
```

### Pitfall 2: Overly Broad Exception Handling
```python
# BAD: Catching too broadly
try:
    result = operation()
except Exception as e:
    handle_error(e)  # Catches everything!

# GOOD: Catch specific exceptions
try:
    result = operation()
except (ValueError, TypeError) as e:
    handle_expected_error(e)
except Exception as e:
    handle_unexpected_error(e)
    raise
```

### Pitfall 3: Missing Context in Errors
```python
# BAD: Error without context
raise ValueError("Invalid data")

# GOOD: Error with context
raise ValueError(f"E022 Invalid data for field '{field_name}': {value}")
```

### Pitfall 4: Not Cleaning Up Resources
```python
# BAD: Resource leak
def process_file(filepath):
    f = open(filepath)
    data = f.read()  # If this fails, file remains open
    return data

# GOOD: Proper resource management
def process_file(filepath):
    try:
        with open(filepath) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to process {filepath}: {e}")
        raise
```

### Pitfall 5: Inconsistent Error Handling
```python
# BAD: Inconsistent error handling
def operation1():
    try:
        return do_something()
    except Exception:
        return None

def operation2():
    try:
        return do_something()
    except Exception as e:
        raise CustomError(f"Failed: {e}")

# GOOD: Consistent error handling pattern
class OperationError(Exception):
    """Base class for operation errors"""
    pass

def operation_with_consistent_errors():
    try:
        return do_something()
    except ValueError as e:
        raise OperationError(f"E030 Invalid input: {e}") from e
    except ConnectionError as e:
        raise OperationError(f"E031 Connection failed: {e}") from e
```

## Summary

Effective error handling is crucial for building robust systems. Key takeaways:

1. **Classify errors** - Use consistent error codes and categories
2. **Handle gracefully** - Provide meaningful error messages and recovery options
3. **Log appropriately** - Capture context for debugging without exposing sensitive data
4. **Test thoroughly** - Include error scenarios in your test suite
5. **Monitor continuously** - Track error rates and patterns
6. **Document clearly** - Maintain error handling documentation

Remember: Good error handling isn't about preventing errors - it's about handling them gracefully when they occur.
