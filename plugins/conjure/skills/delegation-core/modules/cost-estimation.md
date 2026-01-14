---
name: cost-estimation
description: Token cost calculations, budget guidelines, and cost optimization strategies for external LLM delegation
parent_skill: conjure:delegation-core
category: delegation-framework
estimated_tokens: 250
dependencies:
  - leyline:quota-management
  - leyline:usage-logging
---

# Cost Estimation and Budget Guidelines

## Service Cost Comparisons

**Gemini 2.0 Models (per 1M tokens):**
- Input: $0.50, Output: $1.50 (Pro version)
- Input: $0.075, Output: $0.30 (Flash version)
- Context: Up to 1M tokens

**Qwen Models (per 1M tokens):**
- Input: $0.20-0.50, Output: $0.60-1.20 (varies by provider)
- Context: Up to 100K+ tokens
- Sandbox execution: Typically $0.001-0.01 per request

## Cost Decision Framework

**Calculate Cost-Benefit Ratio:**
```
Cost = (input_tokens * input_rate) + (output_tokens * output_rate)
Benefit = time_saved * hourly_rate + quality_improvement_value

Delegate if: Benefit > Cost * 3 (safety margin for quality risks)
```

## Practical Cost Examples

**Low-Cost Delegations (<$0.01):**
- Count function occurrences: 50 files × 30 tokens = $0.000015
- Extract import statements: 100 files × 50 tokens = $0.000025
- Generate 10 boilerplate files: ~2K output tokens = $0.003

**Medium-Cost Delegations ($0.01-0.10):**
- Summarize 50K lines of code: ~125K tokens = $0.06-0.19
- Analyze architecture of 100 files: ~80K tokens = $0.04-0.12
- Generate 20 API endpoints: ~3K output tokens = $0.005

**High-Cost Delegations ($0.10+):**
- Review entire codebase (500K+ tokens): $0.25-0.75
- Generate detailed documentation: $0.15-0.45
- Complex refactoring analysis: $0.20-0.60

## Cost Optimization Strategies

**Input Optimization:**
- Remove comments, tests, examples when not needed
- Use selective file patterns instead of entire directories
- Pre-filter with grep/awk for relevant content
- Compress multiple small queries into one request

**Model Selection:**
- Use Flash/cheaper models for simple extraction tasks
- Reserve Pro models for complex analysis only
- Consider batch processing for repetitive tasks

**Alternative Strategies:**
- Break large tasks into smaller, targeted analyses
- Use local processing for sensitive operations
- Cache results for repeated analysis requests

## Cost Monitoring

**Set Daily/Weekly Budgets:**
- Development: $1-5/day
- Batch processing: $10-50/month
- Enterprise: $100-500/month

**Tracking Methods:**
- Use built-in usage logging tools
- Monitor API dashboard for consumption
- Set up alerts for unexpected spikes

**Using Leyline for Cost Tracking:**

```python
from leyline.quota_tracker import QuotaTracker
from leyline.usage_logger import UsageLogger

# Initialize for your service
tracker = QuotaTracker(service="gemini")
logger = UsageLogger(service="gemini")

# Check quota before operation
level, warnings = tracker.get_quota_status()
if level == "critical":
    # Defer or use secondary logic
    pass

# Log after operation
logger.log_usage("analyze_files", tokens=5000, success=True, duration=2.5)
```
