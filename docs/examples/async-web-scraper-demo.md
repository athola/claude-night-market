# Async Web Scraper Demo

A complete, working example demonstrating async/await patterns in Python for concurrent web scraping. This reference showcases the practical application of python-async skills with real-world functionality.

## Overview

This demo scraper demonstrates:
- Concurrent HTTP requests with aiohttp
- Rate limiting and connection pooling
- Error handling and retries
- Progress tracking and reporting
- Data extraction and storage
- Performance monitoring

## Features

- **Concurrent Scraping**: Process multiple URLs simultaneously
- **Rate Limiting**: Respect server limits with configurable delays
- **Error Resilience**: Handle timeouts, connection errors, and HTTP errors
- **Progress Tracking**: Real-time progress updates
- **Data Export**: Save results in multiple formats (JSON, CSV)
- **Extensible**: Easy to add new data extractors
- **Logging**: detailed logging for debugging and monitoring

## Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/example/async-web-scraper-demo
cd async-web-scraper-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Scrape example URLs
python scraper.py --urls examples/sample_urls.txt

# Scrape with custom concurrency
python scraper.py --urls examples/sample_urls.txt --max-concurrent 5

# Export to CSV
python scraper.py --urls examples/sample_urls.txt --output-format csv

# Run with progress bar
python scraper.py --urls examples/sample_urls.txt --progress
```

## Examples

### Example 1: Basic Scraping
```python
from scraper import AsyncWebScraper

async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/json",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]

    async with AsyncWebScraper() as scraper:
        results = await scraper.scrape_multiple(urls)

        for result in results:
            print(f"{result.url}: {result.title}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Example 2: Custom Data Extraction
```python
from scraper import AsyncWebScraper
from extractors import ProductExtractor, ArticleExtractor

async def scrape_ecommerce():
    scraper = AsyncWebScraper()

    # Add custom extractors for different site types
    scraper.add_extractor('product', ProductExtractor())
    scraper.add_extractor('article', ArticleExtractor())

    urls = [
        "https://example-shop.com/product/123",
        "https://example-blog.com/article/how-to-scrape"
    ]

    results = await scraper.scrape_with_extraction(urls)
    return results
```

### Example 3: Advanced Configuration
```python
from scraper import AsyncWebScraper, Config

async def advanced_scraping():
    config = Config(
        max_concurrent=10,
        rate_limit=1.0,
        timeout=30,
        retries=3,
        retry_delay=5.0,
        user_agent="CustomScraper/1.0"
    )

    async with AsyncWebScraper(config=config) as scraper:
        # Use custom session with proxy
        scraper.session = await scraper.create_session_with_proxy(
            proxy="http://proxy.example.com:8080"
        )

        results = await scraper.scrape_multiple(urls)
        return results
```

## Architecture

### Project Structure
```
async-web-scraper/
├── scraper.py              # Main scraper class
├── config.py              # Configuration management
├── extractors/            # Data extraction modules
│   ├── __init__.py
│   ├── base.py           # Base extractor interface
│   ├── article.py        # Article content extractor
│   ├── product.py        # Product information extractor
│   └── metadata.py       # General metadata extractor
├── storage/              # Data storage modules
│   ├── __init__.py
│   ├── json_storage.py   # JSON file storage
│   ├── csv_storage.py    # CSV file storage
│   └── database.py       # Database storage
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── logger.py         # Logging configuration
│   ├── progress.py       # Progress tracking
│   └── validators.py     # URL and data validation
├── examples/             # Example scripts
└── tests/               # Test files
```

### Key Classes

#### AsyncWebScraper
Main scraper class that orchestrates the scraping process.

```python
class AsyncWebScraper:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.session = None
        self.extractors = {}
        self.stats = ScrapingStats()

    async def scrape_multiple(self, urls: List[str]) -> List[ScrapedData]:
        """Scrape multiple URLs concurrently"""

    async def scrape_with_extraction(self, urls: List[str]) -> List[ExtractedData]:
        """Scrape and extract structured data"""

    def add_extractor(self, name: str, extractor: BaseExtractor):
        """Add custom data extractor"""
```

#### Config
Configuration management for scraper behavior.

```python
@dataclass
class Config:
    max_concurrent: int = 10
    rate_limit: float = 1.0
    timeout: int = 30
    retries: int = 3
    retry_delay: float = 5.0
    user_agent: str = "AsyncWebScraper/1.0"
    headers: Dict[str, str] = field(default_factory=dict)
```

## Performance Tips

### 1. Optimize Concurrency
```python
# Find optimal concurrency for your target
async def find_optimal_concurrency(urls):
    for concurrent in [1, 5, 10, 20, 50]:
        start = time.time()
        results = await scrape_with_concurrency(urls, concurrent)
        duration = time.time() - start
        print(f"Concurrent: {concurrent}, Time: {duration:.2f}s")
```

### 2. Use Connection Pooling
```python
# Configure connection pooling for better performance
connector = aiohttp.TCPConnector(
    limit=100,              # Total connection pool size
    limit_per_host=10,      # Connections per host
    ttl_dns_cache=300,      # DNS cache TTL
    use_dns_cache=True,     # Enable DNS caching
)

session = aiohttp.ClientSession(connector=connector)
```

### 3. Implement Smart Retry Logic
```python
async def smart_retry(request_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await request_func()
        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

## Testing

### Run Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=scraper --cov-report=html

# Run specific test
pytest tests/test_scraper.py::test_scrape_multiple
```

### Test Examples
```python
import pytest
from scraper import AsyncWebScraper

@pytest.mark.asyncio
async def test_scrape_multiple():
    urls = ["https://httpbin.org/json"]

    async with AsyncWebScraper() as scraper:
        results = await scraper.scrape_multiple(urls)

        assert len(results) == 1
        assert results[0].status_code == 200
        assert results[0].title
```

## Related Skills

This demo showcases the practical application of:

- **python-async**: Core async/await patterns
- **python-performance**: Optimization techniques
- **python-testing**: Testing async code
- **context-optimization**: Managing large-scale scraping

## See Also

- [Parseltongue Plugin](../../plugins/parseltongue/) - Python development skills
- [Skill Integration Guide](../skill-integration-guide.md) - Combining skills
