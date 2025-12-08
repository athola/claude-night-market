---
name: python-async
description: Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications.
category: async
tags: [python, async, asyncio, concurrency, await, coroutines]
tools: [async-analyzer, concurrency-checker]
usage_patterns:
  - async-api-development
  - concurrent-io
  - websocket-servers
  - background-tasks
complexity: intermediate
estimated_tokens: 150
progressive_loading: true
modules:
  - basic-patterns
  - concurrency-control
  - error-handling-timeouts
  - advanced-patterns
  - testing-async
  - real-world-applications
  - pitfalls-best-practices
---

# Async Python Patterns

asyncio and async/await patterns for Python applications.

## Quick Start

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

asyncio.run(main())
```

## When to Use

- Building async web APIs (FastAPI, aiohttp)
- Implementing concurrent I/O operations
- Creating web scrapers with concurrent requests
- Developing real-time applications (WebSockets)
- Processing multiple independent tasks simultaneously
- Building microservices with async communication

## Modules

This skill uses progressive loading. Content is organized into focused modules:

- **basic-patterns**: Core async/await, gather(), and task management
- **concurrency-control**: Semaphores and locks for rate limiting
- **error-handling-timeouts**: Error handling, timeouts, and cancellation
- **advanced-patterns**: Context managers, iterators, producer-consumer
- **testing-async**: Testing with pytest-asyncio
- **real-world-applications**: Web scraping and database operations
- **pitfalls-best-practices**: Common mistakes and best practices

Load specific modules based on your needs, or reference all for comprehensive guidance.

## Exit Criteria

- Async patterns applied correctly
- No blocking operations in async code
- Proper error handling implemented
- Rate limiting configured where needed
- Tests pass with pytest-asyncio
