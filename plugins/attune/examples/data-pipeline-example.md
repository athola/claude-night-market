# Data Pipeline Example: Analytics ETL

This example demonstrates architecture-aware initialization for a data processing pipeline.

## Project Scenario

**Project**: Customer Analytics ETL Pipeline
**Team**: 6 data engineers
**Requirements**:
- Extract customer data from multiple sources (APIs, databases, files)
- Transform and enrich with third-party data
- Load into data warehouse for analytics
- Handle 10M+ records daily
- Support incremental and full refresh modes
- Monitoring and error recovery

## Workflow

### Step 1: Architecture-Aware Initialization

```bash
/attune:arch-init --name analytics-pipeline
```

### Interactive Session

```
============================================================
Architecture-Aware Project Initialization
============================================================

Project Context
------------------------------------------------------------

Project Type: 4 (data-pipeline)
Domain Complexity: 2 (Moderate)
Team Size: 2 (5-15)
Programming Language: 1 (Python)
Framework: apache-airflow
Scalability Needs: 3 (High)
Security Requirements: 2 (High)
Time to Market: 2 (Normal)
```

### Research Phase

```
============================================================
Online Research Phase
============================================================

Generated search queries for your project context:
------------------------------------------------------------

1. data-pipeline architecture best practices 2026
   Command: WebSearch("data-pipeline architecture best practices 2026")

2. python data-pipeline architecture patterns 2026
   Command: WebSearch("python data-pipeline architecture patterns 2026")

3. apache-airflow architecture patterns data-pipeline
   Command: WebSearch("apache-airflow architecture patterns data-pipeline")

4. high scalability data-pipeline architecture patterns
   Command: WebSearch("high scalability data-pipeline architecture patterns")

------------------------------------------------------------

Research Focus Areas:
------------------------------------------------------------

  Industry Standards:
    Current architecture patterns for data-pipeline in 2026

  Language Patterns:
    Python-specific best practices and idioms

  Scalability Patterns:
    Horizontal scaling strategies and load distribution

  Framework Integration:
    Apache-Airflow architecture patterns and conventions

  Collaboration Patterns:
    Module ownership and code review strategies
```

### Recommendation

```
============================================================
Architecture Recommendation
============================================================

Primary Paradigm: **Pipeline**
Secondary Paradigm: Event-Driven

Confidence: HIGH

Rationale:
**Selected Based On**: special-case selection (data-processing keyword)
**Team Size**: 5-15
**Domain Complexity**: moderate
**Project Type**: data-pipeline

Trade-offs:
  - **trade-off**: Stage coupling, error handling complexity, state management
  - **mitigation**: Use idempotent stages, implement checkpointing, clear error paths
  - **best-for**: ETL workflows, data processing, sequential transformations
  - **avoid-when**: Non-linear processing, complex branching logic needed

Alternatives Considered:
  - **Event Driven**: Streaming not required, batch sufficient
  - **Serverless**: Long-running stages need persistent compute
  - **Layered**: Linear processing model too rigid

============================================================

Accept this recommendation? [y/n]: y
```

### Generated Project Structure

```
analytics-pipeline/
├── .attune/
│   └── arch-init-session.json
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       └── typecheck.yml
├── docs/
│   └── adr/
│       └── 001-architecture-paradigm.md
├── src/
│   └── analytics_pipeline/
│       ├── stages/                 # Processing stages
│       │   ├── __init__.py
│       │   ├── extract.py         # Data extraction
│       │   ├── transform.py       # Data transformation
│       │   └── load.py            # Data loading
│       ├── pipeline/              # Orchestration
│       │   ├── __init__.py
│       │   ├── orchestrator.py    # Pipeline coordinator
│       │   └── config.py          # Configuration
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
├── dags/                          # Airflow DAGs
│   └── analytics_dag.py
├── .gitignore
├── .pre-commit-config.yaml
├── ARCHITECTURE.md
├── Makefile
├── pyproject.toml
└── README.md
```

## Implementation Guidance

### Extract Stage

```python
# src/analytics_pipeline/stages/extract.py
from dataclasses import dataclass
from typing import Iterator, Protocol
from analytics_pipeline.pipeline.config import SourceConfig

class DataSource(Protocol):
    """Protocol for data sources."""
    def extract(self, config: SourceConfig) -> Iterator[dict]:
        """Extract data from source."""
        ...

@dataclass
class APIExtractor:
    """Extract data from REST APIs."""

    def extract(self, config: SourceConfig) -> Iterator[dict]:
        """Extract data from API endpoint."""
        import requests

        response = requests.get(
            config.endpoint,
            headers=config.headers,
            params=config.params
        )
        response.raise_for_status()

        for record in response.json()['data']:
            yield record

@dataclass
class DatabaseExtractor:
    """Extract data from databases."""

    def extract(self, config: SourceConfig) -> Iterator[dict]:
        """Extract data from database."""
        import sqlalchemy

        engine = sqlalchemy.create_engine(config.connection_string)

        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(config.query))
            for row in result:
                yield dict(row._mapping)

@dataclass
class FileExtractor:
    """Extract data from files."""

    def extract(self, config: SourceConfig) -> Iterator[dict]:
        """Extract data from file."""
        import pandas as pd
        from pathlib import Path

        file_path = Path(config.path)

        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path, chunksize=10000)
            for chunk in df:
                for _, row in chunk.iterrows():
                    yield row.to_dict()
        elif file_path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
            for _, row in df.iterrows():
                yield row.to_dict()
```

### Transform Stage

```python
# src/analytics_pipeline/stages/transform.py
from dataclasses import dataclass
from typing import Iterator, Callable, List
from functools import reduce

@dataclass
class TransformPipeline:
    """Chain of transformations."""
    transformers: List[Callable[[dict], dict]]

    def transform(self, records: Iterator[dict]) -> Iterator[dict]:
        """Apply all transformations to records."""
        for record in records:
            try:
                result = reduce(
                    lambda r, t: t(r),
                    self.transformers,
                    record
                )
                yield result
            except Exception as e:
                yield {"_error": str(e), "_original": record}

# Individual transformers
def normalize_dates(record: dict) -> dict:
    """Normalize date fields to ISO format."""
    from datetime import datetime

    date_fields = ['created_at', 'updated_at', 'order_date']
    result = record.copy()

    for field in date_fields:
        if field in result and result[field]:
            parsed = datetime.fromisoformat(str(result[field]))
            result[field] = parsed.isoformat()

    return result

def enrich_customer(record: dict) -> dict:
    """Enrich customer data with derived fields."""
    result = record.copy()

    if 'email' in result:
        result['email_domain'] = result['email'].split('@')[-1]

    if 'total_orders' in result and 'total_spent' in result:
        if result['total_orders'] > 0:
            result['avg_order_value'] = result['total_spent'] / result['total_orders']

    return result

def validate_required_fields(record: dict) -> dict:
    """Validate required fields are present."""
    required = ['customer_id', 'email']

    missing = [f for f in required if f not in record or not record[f]]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    return record
```

### Load Stage

```python
# src/analytics_pipeline/stages/load.py
from dataclasses import dataclass
from typing import Iterator, List
from analytics_pipeline.pipeline.config import TargetConfig

@dataclass
class WarehouseLoader:
    """Load data into data warehouse."""
    batch_size: int = 1000

    def load(
        self,
        records: Iterator[dict],
        config: TargetConfig
    ) -> dict:
        """Load records into warehouse."""
        import sqlalchemy

        engine = sqlalchemy.create_engine(config.connection_string)
        batch: List[dict] = []
        stats = {"inserted": 0, "errors": 0}

        for record in records:
            if "_error" in record:
                stats["errors"] += 1
                self._log_error(record)
                continue

            batch.append(record)

            if len(batch) >= self.batch_size:
                self._insert_batch(engine, config.table, batch)
                stats["inserted"] += len(batch)
                batch = []

        if batch:
            self._insert_batch(engine, config.table, batch)
            stats["inserted"] += len(batch)

        return stats

    def _insert_batch(self, engine, table: str, batch: List[dict]):
        """Insert a batch of records."""
        import pandas as pd

        df = pd.DataFrame(batch)
        df.to_sql(table, engine, if_exists='append', index=False)

    def _log_error(self, record: dict):
        """Log error record for later review."""
        import logging
        logging.error(f"Failed record: {record}")
```

### Pipeline Orchestrator

```python
# src/analytics_pipeline/pipeline/orchestrator.py
from dataclasses import dataclass
from typing import Optional
from analytics_pipeline.stages.extract import DataSource, APIExtractor, DatabaseExtractor
from analytics_pipeline.stages.transform import (
    TransformPipeline,
    normalize_dates,
    enrich_customer,
    validate_required_fields
)
from analytics_pipeline.stages.load import WarehouseLoader
from analytics_pipeline.pipeline.config import PipelineConfig

@dataclass
class PipelineOrchestrator:
    """Orchestrate the ETL pipeline."""
    config: PipelineConfig

    def run(self, source_name: Optional[str] = None) -> dict:
        """Run the complete pipeline."""
        results = {}

        sources = (
            [source_name] if source_name
            else self.config.sources.keys()
        )

        for name in sources:
            source_config = self.config.sources[name]
            extractor = self._get_extractor(source_config.type)

            # Extract
            records = extractor.extract(source_config)

            # Transform
            transformer = TransformPipeline([
                normalize_dates,
                enrich_customer,
                validate_required_fields
            ])
            transformed = transformer.transform(records)

            # Load
            loader = WarehouseLoader(batch_size=self.config.batch_size)
            stats = loader.load(transformed, self.config.target)

            results[name] = stats

        return results

    def _get_extractor(self, source_type: str) -> DataSource:
        """Get appropriate extractor for source type."""
        extractors = {
            "api": APIExtractor(),
            "database": DatabaseExtractor(),
        }
        return extractors[source_type]
```

### Airflow DAG

```python
# dags/analytics_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from analytics_pipeline.pipeline.orchestrator import PipelineOrchestrator
from analytics_pipeline.pipeline.config import PipelineConfig

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def run_pipeline(**kwargs):
    """Run the analytics pipeline."""
    config = PipelineConfig.from_file('config/pipeline.yaml')
    orchestrator = PipelineOrchestrator(config)
    return orchestrator.run()

with DAG(
    'analytics_etl',
    default_args=default_args,
    description='Customer analytics ETL pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['analytics', 'etl'],
) as dag:

    extract_transform_load = PythonOperator(
        task_id='run_pipeline',
        python_callable=run_pipeline,
    )
```

## Why Pipeline Architecture?

For this data pipeline project:

1. **Natural Fit**: ETL workflows map directly to Extract -> Transform -> Load stages
2. **Testability**: Each stage can be tested independently
3. **Monitoring**: Clear stage boundaries make it easy to monitor progress
4. **Recovery**: Checkpointing between stages enables restart from failure point
5. **Scalability**: Stages can be parallelized or distributed as data grows

## Error Handling Pattern

```python
# src/analytics_pipeline/pipeline/recovery.py
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Checkpoint:
    """Pipeline checkpoint for recovery."""
    stage: str
    position: int
    state: dict

    def save(self, path: Path):
        """Save checkpoint to file."""
        path.write_text(json.dumps({
            "stage": self.stage,
            "position": self.position,
            "state": self.state
        }))

    @classmethod
    def load(cls, path: Path) -> 'Checkpoint':
        """Load checkpoint from file."""
        data = json.loads(path.read_text())
        return cls(**data)
```

## Next Steps

After initialization:

1. **Set up development environment**:
   ```bash
   cd analytics-pipeline
   make dev-setup
   ```

2. **Configure data sources**:
   ```bash
   cp config/pipeline.example.yaml config/pipeline.yaml
   # Edit config/pipeline.yaml with your sources
   ```

3. **Test individual stages**:
   ```bash
   make test
   ```

4. **Deploy to Airflow**:
   ```bash
   make deploy-dag
   ```

## When to Consider Event-Driven

If requirements include:
- Real-time or near-real-time processing
- Complex event routing based on content
- Multiple consumers for the same data

Consider combining with event-driven architecture:

```bash
/attune:arch-init --name analytics-pipeline --arch event-driven
```

This would add Kafka/Pulsar integration for streaming data.
