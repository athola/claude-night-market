# Conservation Plugin Integration Guide

## Overview

Conservation v2.0 now provides enhanced context optimization with condition-based waiting, eliminating flaky optimization behavior. Other plugins can easily integrate with Conservation to:

1. **Optimize content** with reliable condition-based waiting
2. **Monitor context pressure** without arbitrary delays
3. **Coordinate optimization** across multiple plugins
4. **Get MECW-compliant** optimization strategies

## Quick Start for Plugin Developers

### 1. Basic Integration (3 lines of code)

```python
# In your plugin code
from conservation.services.optimization_service import optimize_content

# Optimize your content
result = optimize_content(
    plugin_name="your_plugin_name",
    content=your_long_content,
    max_tokens=2000,
    strategy="priority"
)

# Use optimized content
optimized = result["optimized_content"]
```

### 2. Advanced Integration with Monitoring

```python
from conservation.services.optimization_service import (
    optimize_content,
    monitor_context,
    coordinate_plugins
)

# Monitor context pressure before optimization
pressure = monitor_context(threshold=0.7, plugin_name="your_plugin")

if pressure["usage"] > 0.7:
    # Coordinate with other plugins if needed
    coordination = coordinate_plugins(
        plugins=["your_plugin", "other_relevant_plugins"],
        optimization_type="resource"
    )

    # Optimize with condition-based waiting
    result = optimize_content(
        plugin_name="your_plugin",
        content=your_content,
        max_tokens=1500,  # More aggressive due to pressure
        strategy="importance"  # Keep important content
    )
```

## Integration Patterns for Common Use Cases

### Pattern 1: Proactive Content Optimization

**When to use**: Your plugin generates or processes large amounts of content

```python
class YourPluginProcessor:
    def __init__(self):
        # Import Conservation services
        from conservation.services.optimization_service import (
            optimize_content,
            monitor_context
        )

        self.optimize = optimize_content
        self.monitor = monitor_context

    def process_large_content(self, content, plugin_name):
        """Process content with Conservation optimization"""

        # Step 1: Check context pressure
        try:
            pressure = self.monitor(
                threshold=0.6,
                plugin_name=plugin_name
            )

            # Adjust optimization based on pressure
            if pressure["pressure_level"] == "high":
                max_tokens = 1000
                strategy = "priority"
            elif pressure["pressure_level"] == "moderate":
                max_tokens = 1500
                strategy = "balanced"
            else:
                max_tokens = 2500
                strategy = "semantic"

            # Step 2: Optimize with condition-based waiting
            result = self.optimize(
                plugin_name=plugin_name,
                content=content,
                max_tokens=max_tokens,
                strategy=strategy
            )

            # Step 3: Use optimized content
            if result["status"] == "completed":
                return result["optimized_content"]
            else:
                # Fallback to original content
                return content

        except TimeoutError:
            # Context monitoring timed out, use conservative optimization
            result = self.optimize(
                plugin_name=plugin_name,
                content=content,
                max_tokens=800,
                strategy="priority"
            )
            return result.get("optimized_content", content)
```

### Pattern 2: Multi-Plugin Coordination

**When to use**: Your plugin needs to coordinate resource usage with other plugins

```python
class CoordinatedPluginManager:
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name

        # Import Conservation coordination services
        from conservation.services.optimization_service import (
            coordinate_plugins,
            optimize_content
        )

        self.coordinate = coordinate_plugins
        self.optimize = optimize_content

    def coordinate_resource_usage(self, content, related_plugins):
        """Coordinate optimization across related plugins"""

        # Step 1: Coordinate with other plugins
        coordination = self.coordinate(
            plugins=[self.plugin_name] + related_plugins,
            optimization_type="resource"
        )

        if not coordination["coordination_successful"]:
            # Some plugins not ready, reduce resource usage
            max_tokens = 1000
        else:
            # All plugins ready, can use more resources
            max_tokens = 2000

        # Step 2: Optimize with coordinated limits
        result = self.optimize(
            plugin_name=self.plugin_name,
            content=content,
            max_tokens=max_tokens,
            strategy="balanced"
        )

        return {
            "optimized_content": result.get("optimized_content", content),
            "coordination_info": coordination,
            "resource_usage": {
                "tokens_used": result.get("metrics", {}).get("optimized_tokens", 0),
                "plugins_coordinated": len(coordination["coordinated_plugins"])
            }
        }
```

### Pattern 3: Continuous Monitoring and Adaptive Optimization

**When to use**: Your plugin runs continuously and needs to adapt to changing context

```python
class AdaptiveOptimizationManager:
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.optimization_history = []

        # Import Conservation services
        from conservation.services.optimization_service import (
            optimize_content,
            monitor_context,
            get_conservation_services
        )

        self.optimize = optimize_content
        self.monitor = monitor_context
        self.services = get_conservation_services()

    def adaptive_optimize(self, content, importance_level="normal"):
        """Adapt optimization based on current conditions and history"""

        # Step 1: Discover best strategy based on conditions
        pressure = self._check_pressure()
        strategy = self._select_strategy(pressure, importance_level)

        # Step 2: Calculate optimal token limit
        max_tokens = self._calculate_token_limit(pressure, importance_level)

        # Step 3: Optimize with condition-based waiting
        start_time = time.time()
        result = self.optimize(
            plugin_name=self.plugin_name,
            content=content,
            max_tokens=max_tokens,
            strategy=strategy
        )

        # Step 4: Record results for learning
        self.optimization_history.append({
            "timestamp": start_time,
            "pressure": pressure,
            "strategy": strategy,
            "max_tokens": max_tokens,
            "result": result,
            "duration": time.time() - start_time
        })

        # Step 5: Adapt future strategies based on results
        self._adapt_strategies()

        return result

    def _check_pressure(self):
        """Check current context pressure"""
        try:
            pressure = self.monitor(
                threshold=0.5,
                plugin_name=self.plugin_name
            )
            return pressure["pressure_level"]
        except TimeoutError:
            return "low"  # No pressure detected

    def _select_strategy(self, pressure, importance):
        """Select optimization strategy based on conditions"""
        strategy_map = {
            ("high", "critical"): "priority",
            ("high", "normal"): "priority",
            ("high", "low"): "balanced",
            ("moderate", "critical"): "importance",
            ("moderate", "normal"): "balanced",
            ("moderate", "low"): "semantic",
            ("low", "critical"): "semantic",
            ("low", "normal"): "balanced",
            ("low", "low"): "recency"
        }
        return strategy_map.get((pressure, importance), "balanced")

    def _calculate_token_limit(self, pressure, importance):
        """Calculate appropriate token limit"""
        base_limits = {
            "critical": 2000,
            "normal": 1500,
            "low": 1000
        }

        pressure_multipliers = {
            "high": 0.6,
            "moderate": 0.8,
            "low": 1.0
        }

        base = base_limits.get(importance, 1500)
        multiplier = pressure_multipliers.get(pressure, 1.0)

        return int(base * multiplier)

    def _adapt_strategies(self):
        """Learn from optimization history and adapt"""
        if len(self.optimization_history) < 5:
            return  # Need more data

        # Analyze recent optimizations
        recent = self.optimization_history[-5:]
        avg_duration = sum(r["duration"] for r in recent) / len(recent)
        success_rate = sum(1 for r in recent if r["result"]["status"] == "completed") / len(recent)

        # Adapt based on performance
        if success_rate < 0.8:
            # Reduce token limits for better success rate
            for record in self.optimization_history[-3:]:
                record["max_tokens"] = int(record["max_tokens"] * 0.8)

        if avg_duration > 10:  # Taking too long
            # Use faster strategies
            for record in self.optimization_history[-3:]:
                if record["strategy"] == "semantic":
                    record["strategy"] = "balanced"
```

## Advanced Integration Examples

### Example 1: Abstract Plugin Integration

```python
# In abstract/skills/analyze-skill.py
from conservation.services.optimization_service import (
    optimize_content,
    monitor_context,
    coordinate_plugins
)

def analyze_with_optimization(skill_content, skill_name):
    """Analyze skill with Conservation optimization"""

    # Monitor context pressure before analysis
    pressure = monitor_context(
        threshold=0.6,
        plugin_name="abstract"
    )

    # Prepare content for optimization
    content_blocks = [
        {
            "content": skill_content.get("skill_definition", ""),
            "priority": 0.9,
            "source": "skill_definition",
            "metadata": {"section": "core"}
        },
        {
            "content": skill_content.get("examples", ""),
            "priority": 0.6,
            "source": "examples",
            "metadata": {"section": "examples"}
        },
        {
            "content": skill_content.get("documentation", ""),
            "priority": 0.4,
            "source": "documentation",
            "metadata": {"section": "docs"}
        }
    ]

    # Optimize based on context pressure
    strategy = "priority" if pressure.get("pressure_level") == "high" else "balanced"
    max_tokens = 1500 if pressure.get("pressure_level") == "high" else 2500

    result = optimize_content(
        plugin_name="abstract",
        content=content_blocks,
        max_tokens=max_tokens,
        strategy=strategy
    )

    # Perform analysis on optimized content
    if result["status"] == "completed":
        return analyze_optimized_skill(result["optimized_content"], skill_name)
    else:
        # Fallback analysis
        return analyze_skill_directly(skill_content, skill_name)
```

### Example 2: Sanctum Plugin Integration

```python
# In sanctum/skills/commit-messages.py
from conservation.services.optimization_service import (
    optimize_content,
    coordinate_plugins
)

def optimize_commit_message_with_conservation(diff_content, commit_message):
    """Optimize commit message and diff with Conservation"""

    # Coordinate with related plugins
    coordination = coordinate_plugins(
        plugins=["sanctum", "imbue", "abstract"],
        optimization_type="git_workflow"
    )

    # Optimize commit message
    message_result = optimize_content(
        plugin_name="sanctum",
        content=commit_message,
        max_tokens=200,  # Short messages
        strategy="priority"
    )

    # Optimize diff if needed
    diff_tokens = len(diff_content.split()) * 1.3
    if diff_tokens > 1000:
        diff_result = optimize_content(
            plugin_name="sanctum",
            content=diff_content,
            max_tokens=800,
            strategy="importance"
        )
        optimized_diff = diff_result["optimized_content"]
    else:
        optimized_diff = diff_content

    return {
        "optimized_message": message_result.get("optimized_content", commit_message),
        "optimized_diff": optimized_diff,
        "coordination": coordination
    }
```

## Configuration and Customization

### Custom Optimization Strategies

```python
# Register custom strategy with Conservation
from conservation.services.optimization_service import optimization_service
from conservation.skills.context_optimization.condition_based_optimizer import ContentBlock

def custom_strategy(blocks, max_tokens):
    """Custom optimization strategy for your plugin"""
    # Your custom logic here
    # Example: Prioritize blocks from your plugin
    plugin_blocks = [b for b in blocks if b.source == "your_plugin"]
    other_blocks = [b for b in blocks if b.source != "your_plugin"]

    # Keep all your plugin blocks first
    result = []
    current_tokens = 0

    for block in plugin_blocks:
        if current_tokens + block.token_estimate <= max_tokens:
            result.append(block)
            current_tokens += block.token_estimate

    # Fill with other blocks if space allows
    for block in other_blocks:
        if current_tokens + block.token_estimate <= max_tokens:
            result.append(block)
            current_tokens += block.token_estimate

    return result

# Register your strategy
optimization_service.optimizer.strategies["custom_plugin"] = custom_strategy
```

### Plugin-Specific Configuration

```python
# Create plugin-specific optimization config
PLUGIN_CONFIGS = {
    "abstract": {
        "default_strategy": "importance",
        "max_tokens": 2000,
        "priority_keywords": ["function", "class", "import"],
        "preserve_structure": True
    },
    "sanctum": {
        "default_strategy": "priority",
        "max_tokens": 1500,
        "priority_keywords": ["commit", "diff", "merge"],
        "preserve_structure": False
    },
    "imbue": {
        "default_strategy": "semantic",
        "max_tokens": 1800,
        "priority_keywords": ["review", "analysis", "summary"],
        "preserve_structure": True
    }
}

def get_plugin_config(plugin_name):
    """Get optimization configuration for a plugin"""
    return PLUGIN_CONFIGS.get(plugin_name, {
        "default_strategy": "balanced",
        "max_tokens": 1500,
        "priority_keywords": [],
        "preserve_structure": True
    })
```

## Best Practices

### 1. Always Handle Optimization Failures

```python
def safe_optimize(plugin_name, content, max_tokens, strategy="balanced"):
    """Safe optimization with fallback"""
    try:
        result = optimize_content(
            plugin_name=plugin_name,
            content=content,
            max_tokens=max_tokens,
            strategy=strategy
        )

        if result["status"] == "completed":
            return result["optimized_content"]
        else:
            # Log the failure and return original
            log_optimization_failure(result)
            return content

    except Exception as e:
        # Conservation service unavailable
        log_service_error(e)
        return content
```

### 2. Monitor Performance Metrics

```python
def monitor_optimization_performance():
    """Track optimization performance across your plugin"""
    from conservation.services.optimization_service import optimization_service

    # Get optimization history if available
    if hasattr(optimization_service.optimizer, 'active_optimizations'):
        active = len(optimization_service.optimizer.active_optimizations)

        # Adjust behavior based on active optimizations
        if active > 5:
            # System is busy, be more conservative
            return {"max_tokens": 1000, "strategy": "priority"}
        else:
            # System has capacity
            return {"max_tokens": 2000, "strategy": "balanced"}

    return {"max_tokens": 1500, "strategy": "balanced"}
```

### 3. Coordinate with Other Plugins

```python
def collaborative_optimization(content, plugin_name):
    """Collaborate with other plugins for better results"""

    # Discover related plugins
    related_plugins = discover_related_plugins(plugin_name)

    # Coordinate optimization
    coordination = coordinate_plugins(
        plugins=[plugin_name] + related_plugins,
        optimization_type="collaborative"
    )

    # Adjust based on coordination results
    if coordination["coordination_successful"]:
        # Can be more aggressive with coordination
        max_tokens = 2500
        strategy = "semantic"
    else:
        # Be conservative
        max_tokens = 1200
        strategy = "priority"

    return optimize_content(
        plugin_name=plugin_name,
        content=content,
        max_tokens=max_tokens,
        strategy=strategy
    )
```

## Troubleshooting

### Common Issues and Solutions

1. **TimeoutError during optimization**
   - Reduce max_tokens
   - Use faster strategy (priority > balanced > semantic)
   - Check system load

2. **Poor compression ratio**
   - Try different strategy
   - Adjust content priorities
   - Check if content is already optimized

3. **Coordination failures**
   - Increase timeout for coordination
   - Check if other plugins are responsive
   - Fall back to independent optimization

### Debug Mode

```python
# Enable debug mode for detailed logging
import logging
logging.getLogger("conservation").setLevel(logging.DEBUG)

# Optimization will now show detailed information
result = optimize_content(
    plugin_name="debug_plugin",
    content=test_content,
    max_tokens=1000,
    strategy="balanced"
)
```

## Getting Help

- Check Conservation plugin documentation in `/docs/`
- Use `get_conservation_services()` to discover available services
- Monitor service status with condition-based waiting functions
- Report issues to the Conservation plugin maintainers

## Version Compatibility

This integration guide is for Conservation v2.0 with:
- Condition-based waiting (no arbitrary timeouts)
- MECW compliance (50% context rule)
- Plugin coordination support
- Async optimization capabilities

Older versions may have different interfaces and capabilities.
