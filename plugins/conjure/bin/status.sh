#!/bin/bash
# Gemini CLI Status Monitor

echo "**Gemini CLI Status Report**"
echo "=================================="
echo

# Check quota status
echo "**Quota Status**:"
python3 ~/.claude/hooks/gemini/quota_tracker.py 2>/dev/null || echo "  Quota tracker unavailable"
echo

# Check usage summary
echo "**Usage Summary (24h)**:"
python3 -c "
from usage_logger import GeminiUsageLogger
import json
try:
    logger = GeminiUsageLogger()
    summary = logger.get_usage_summary()
    print(f'  Requests: {summary[\"total_requests\"]}')
    print(f'  Tokens: {summary[\"total_tokens\"]:,}')
    print(f'  Success Rate: {summary[\"success_rate\"]:.1f}%')
except Exception as e:
    print(f'  Error: {e}')
" 2>/dev/null || echo "  Usage logger unavailable"
echo

# Check recent errors
echo "**Recent Errors**:"
python3 -c "
from usage_logger import GeminiUsageLogger
import json
try:
    logger = GeminiUsageLogger()
    errors = logger.get_recent_errors(3)
    if errors:
        for error in errors[-3:]:
            timestamp = error['timestamp'].split('T')[1][:8]
            print(f'  {timestamp}: {error[\"error\"]}')
    else:
        print('  No recent errors')
except Exception:
    print('  No error data available')
" 2>/dev/null || echo "  Error log unavailable"
echo

# Check authentication
echo "**Authentication**:"
if gemini auth status &>/dev/null; then
    echo "  Authenticated"
else
    echo "  Not authenticated or quota exhausted"
fi
echo

echo "**Quick Commands**:"
echo "  • Monitor quota: python3 ~/.claude/hooks/gemini/quota_tracker.py"
echo "  • View usage: python3 -c 'from usage_logger import GeminiUsageLogger; print(GeminiUsageLogger().get_usage_summary())'"
echo "  • Check auth: gemini auth status"
