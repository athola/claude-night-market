---
name: monitoring-patterns
description: Advanced patterns for continuous MECW monitoring, integration patterns, and proactive context management
category: patterns
parent_skill: leyline:mecw-patterns
estimated_tokens: 850
reusable_by: [conservation, conjure, spec-kit, abstract]
tags: [monitoring, integration, automation, alerting]
---

# MECW Monitoring Patterns

## Continuous Monitoring Architecture

Effective MECW management requires continuous monitoring rather than reactive checks.

### Basic Monitoring Loop

```python
from leyline import MECWMonitor

class ContextAwareAgent:
    def __init__(self):
        self.mecw = MECWMonitor(max_context=200000)

    def execute_workflow(self, operations):
        for i, operation in enumerate(operations):
            # Monitor before each operation
            status = self.mecw.get_status()

            if status.pressure_level == "CRITICAL":
                # Emergency: reset context
                self.save_state()
                self.reset_context()
                self.mecw.reset()

            elif status.pressure_level == "HIGH":
                # Optimize before proceeding
                self.optimize_context()

            # Execute with monitoring
            result = self.execute_operation(operation)

            # Track new usage
            new_tokens = self.estimate_operation_tokens(operation, result)
            self.mecw.track_usage(self.mecw.current_tokens + new_tokens)
```

### Predictive Monitoring

Look ahead to prevent issues:

```python
class PredictiveMonitor:
    def __init__(self):
        self.mecw = MECWMonitor()
        self.operation_history = []

    def can_handle_workflow(self, operations):
        """Check if entire workflow fits within MECW."""
        # Estimate total tokens needed
        total_estimated = sum(
            self.estimate_operation(op) for op in operations
        )

        # Check if we can handle it
        can_proceed, issues = self.mecw.can_handle_additional(
            total_estimated
        )

        if not can_proceed:
            # Calculate how to split
            chunks = self.split_into_mecw_chunks(operations)
            return {
                'direct': False,
                'chunks': len(chunks),
                'strategy': 'delegate_to_subagents',
                'issues': issues
            }

        return {'direct': True, 'strategy': 'execute_directly'}

    def split_into_mecw_chunks(self, operations):
        """Split operations into MECW-compliant chunks."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        safe_budget = self.mecw.get_safe_budget()

        for op in operations:
            op_tokens = self.estimate_operation(op)

            if current_tokens + op_tokens > safe_budget:
                # Start new chunk
                chunks.append(current_chunk)
                current_chunk = [op]
                current_tokens = op_tokens
            else:
                current_chunk.append(op)
                current_tokens += op_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
```

## Graduated Response Patterns

Different pressure levels require different responses.

### Response Matrix

```python
RESPONSE_STRATEGIES = {
    "LOW": {
        "action": "continue",
        "monitoring_interval": "every_10_operations",
        "optimization": "none"
    },
    "MODERATE": {
        "action": "monitor_closely",
        "monitoring_interval": "every_5_operations",
        "optimization": "opportunistic"  # Optimize when convenient
    },
    "HIGH": {
        "action": "optimize_proactively",
        "monitoring_interval": "every_operation",
        "optimization": "aggressive"  # Optimize before proceeding
    },
    "CRITICAL": {
        "action": "emergency_reset",
        "monitoring_interval": "continuous",
        "optimization": "mandatory"  # Cannot proceed without optimization
    }
}

class GraduatedMonitor:
    def __init__(self):
        self.mecw = MECWMonitor()

    def handle_pressure(self):
        status = self.mecw.get_status()
        strategy = RESPONSE_STRATEGIES[status.pressure_level]

        if strategy["action"] == "emergency_reset":
            self.emergency_reset()
        elif strategy["action"] == "optimize_proactively":
            self.aggressive_optimize()
        elif strategy["action"] == "monitor_closely":
            self.increase_monitoring_frequency()
        else:
            self.continue_normally()
```

### Optimization Strategies by Pressure

```python
class ContextOptimizer:
    def optimize_for_pressure(self, pressure_level):
        """Apply appropriate optimization for pressure level."""

        if pressure_level == "CRITICAL":
            # Emergency: aggressive compression
            self.summarize_all_completed_work()
            self.remove_all_intermediate_results()
            self.keep_only_essential_context()

        elif pressure_level == "HIGH":
            # Proactive: significant compression
            self.summarize_completed_sections()
            self.remove_redundant_information()
            self.compress_verbose_outputs()

        elif pressure_level == "MODERATE":
            # Opportunistic: gentle compression
            self.remove_obvious_redundancies()
            self.compress_repetitive_data()

        else:  # LOW
            # Preventive: maintain good hygiene
            self.clean_up_temporary_data()
```

## Integration Patterns

### With Workflow Orchestration

```python
from leyline import MECWMonitor, estimate_tokens

class WorkflowOrchestrator:
    def __init__(self):
        self.mecw = MECWMonitor()

    def execute_plan(self, tasks):
        """Execute task plan with MECW awareness."""

        for task in tasks:
            # Estimate task cost
            estimated_tokens = estimate_tokens(
                files=task.files,
                prompt=task.prompt
            )

            # Check MECW compliance
            can_proceed, issues = self.mecw.can_handle_additional(
                estimated_tokens
            )

            if can_proceed:
                # Direct execution
                result = self.execute_task(task)
                self.mecw.track_usage(
                    self.mecw.current_tokens + estimated_tokens
                )
            else:
                # Delegate to subagent
                result = self.delegate_to_subagent(task)
                # Subagent has fresh context - only track result size
                result_tokens = estimate_tokens([], str(result))
                self.mecw.track_usage(
                    self.mecw.current_tokens + result_tokens
                )

        return self.compile_results()
```

### With Session Management

```python
class SessionManager:
    def __init__(self):
        self.mecw = MECWMonitor()
        self.checkpoints = []

    def checkpoint_if_needed(self):
        """Create checkpoint before MECW limits."""
        status = self.mecw.get_status()

        if status.pressure_level in ["HIGH", "CRITICAL"]:
            # Save current state
            checkpoint = {
                'timestamp': datetime.now(),
                'context_state': self.serialize_context(),
                'pressure_level': status.pressure_level,
                'tokens': self.mecw.current_tokens
            }
            self.checkpoints.append(checkpoint)

            # Suggest reset
            print(f"Checkpoint created. Consider /clear and resume.")
            return checkpoint

        return None

    def resume_from_checkpoint(self, checkpoint):
        """Resume from checkpoint with fresh context."""
        self.load_context(checkpoint['context_state'])
        self.mecw.reset()  # Fresh context window
        self.mecw.track_usage(
            self.estimate_loaded_context()
        )
```

## Alerting and Reporting

### Real-time Alerts

```python
class MECWAlerting:
    def __init__(self):
        self.mecw = MECWMonitor()
        self.alert_thresholds = {
            'MODERATE': False,  # Alert once when entering MODERATE
            'HIGH': True,       # Alert every time in HIGH
            'CRITICAL': True    # Alert every time in CRITICAL
        }

    def check_and_alert(self):
        status = self.mecw.get_status()

        if status.warnings:
            for warning in status.warnings:
                self.emit_alert(
                    level=status.pressure_level,
                    message=warning
                )

        if status.recommendations:
            self.emit_recommendations(status.recommendations)

    def emit_alert(self, level, message):
        """Emit alert based on severity."""
        icons = {
            'LOW': '[INFO]',
            'MODERATE': '[WARN]',
            'HIGH': '[HIGH]',
            'CRITICAL': '[CRIT]'
        }
        print(f"{icons[level]} {level}: {message}")
```

### Progress Reports

```python
class ProgressReporter:
    def __init__(self):
        self.mecw = MECWMonitor()

    def report_status(self):
        """Generate human-readable status report."""
        status = self.mecw.get_status()

        print("\n=== MECW Status Report ===")
        print(f"Pressure Level: {status.pressure_level}")
        print(f"Usage: {status.usage_ratio:.1f}%")
        print(f"Headroom: {status.headroom:,} tokens")
        print(f"Safe Budget: {self.mecw.get_safe_budget():,} tokens")

        if status.warnings:
            print("\nWarnings:")
            for warning in status.warnings:
                print(f"  - {warning}")

        if status.recommendations:
            print("\nRecommendations:")
            for rec in status.recommendations:
                print(f"  - {rec}")

        print("=" * 30 + "\n")
```

## Best Practices

### 1. Monitor Before Major Operations

```python
def execute_major_operation(self, operation):
    # Always check before, not after
    status = self.mecw.get_status()

    if status.pressure_level in ["HIGH", "CRITICAL"]:
        raise ContextPressureError(
            f"Cannot proceed with {status.pressure_level} pressure"
        )

    # Execute operation
    result = self.perform_operation(operation)

    # Update tracking
    self.mecw.track_usage(self.calculate_new_total())

    return result
```

### 2. Implement Circuit Breakers

```python
class CircuitBreaker:
    def __init__(self):
        self.mecw = MECWMonitor()
        self.consecutive_high_pressure = 0

    def check_circuit(self):
        status = self.mecw.get_status()

        if status.pressure_level in ["HIGH", "CRITICAL"]:
            self.consecutive_high_pressure += 1
        else:
            self.consecutive_high_pressure = 0

        # Trip circuit after 3 consecutive high pressure operations
        if self.consecutive_high_pressure >= 3:
            raise CircuitBreakerTripped(
                "Too many consecutive high-pressure operations"
            )
```

### 3. Trend Analysis

```python
class TrendAnalyzer:
    def analyze_growth_trend(self, monitor):
        """Analyze token growth trends."""
        history = monitor._usage_history

        if len(history) < 3:
            return "insufficient_data"

        # Calculate growth rate
        recent_growth = history[-1] - history[-3]
        growth_rate = recent_growth / 2  # per operation

        # Project future
        operations_until_mecw = (
            monitor.mecw_threshold - monitor.current_tokens
        ) / growth_rate

        if operations_until_mecw < 5:
            return "critical_growth"
        elif operations_until_mecw < 10:
            return "high_growth"
        elif operations_until_mecw < 20:
            return "moderate_growth"
        else:
            return "sustainable_growth"
```

## Testing and Validation

### Unit Testing MECW Logic

```python
def test_mecw_monitoring():
    monitor = MECWMonitor(max_context=100000)

    # Test LOW pressure
    monitor.track_usage(20000)
    assert monitor.get_status().pressure_level == "LOW"

    # Test MODERATE pressure
    monitor.track_usage(40000)
    assert monitor.get_status().pressure_level == "MODERATE"

    # Test HIGH pressure
    monitor.track_usage(60000)
    status = monitor.get_status()
    assert status.pressure_level == "HIGH"
    assert not status.compliant

    # Test CRITICAL pressure
    monitor.track_usage(80000)
    status = monitor.get_status()
    assert status.pressure_level == "CRITICAL"
    assert len(status.recommendations) > 0
```

## Performance Considerations

The monitoring itself should be lightweight:

```python
# Monitoring overhead: ~0.1ms per check
# Memory overhead: ~1KB per monitor instance
# Safe to check on every operation
```

Use monitoring strategically:
- Check before potentially large operations
- Skip monitoring for trivial operations
- Batch small operations, check periodically
