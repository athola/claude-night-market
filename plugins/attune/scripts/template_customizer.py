#!/usr/bin/env python3
"""Customize project templates based on selected architecture paradigm."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateCustomizer:
    """Customize project templates for specific architecture paradigms."""

    # Architecture-specific directory structures
    STRUCTURE_TEMPLATES: dict[str, dict[str, Any]] = {
        "functional-core": {
            "description": "Functional Core, Imperative Shell - separate pure logic from side effects",
            "python_structure": [
                "src/{module}/core/__init__.py",
                "src/{module}/core/domain.py",
                "src/{module}/core/operations.py",
                "src/{module}/core/commands.py",
                "src/{module}/adapters/__init__.py",
                "src/{module}/adapters/database.py",
                "src/{module}/adapters/api.py",
                "src/{module}/adapters/filesystem.py",
            ],
            "rust_structure": [
                "src/core/mod.rs",
                "src/core/domain.rs",
                "src/core/operations.rs",
                "src/core/commands.rs",
                "src/adapters/mod.rs",
                "src/adapters/database.rs",
                "src/adapters/api.rs",
            ],
            "typescript_structure": [
                "src/core/domain.ts",
                "src/core/operations.ts",
                "src/core/commands.ts",
                "src/adapters/database.ts",
                "src/adapters/api.ts",
            ],
        },
        "hexagonal": {
            "description": "Hexagonal Architecture (Ports & Adapters) - infrastructure independence",
            "python_structure": [
                "src/{module}/domain/__init__.py",
                "src/{module}/domain/models.py",
                "src/{module}/domain/services.py",
                "src/{module}/domain/ports/__init__.py",
                "src/{module}/domain/ports/input.py",
                "src/{module}/domain/ports/output.py",
                "src/{module}/infrastructure/__init__.py",
                "src/{module}/infrastructure/persistence/__init__.py",
                "src/{module}/infrastructure/persistence/repositories.py",
                "src/{module}/infrastructure/web/__init__.py",
                "src/{module}/infrastructure/web/controllers.py",
                "src/{module}/infrastructure/messaging/__init__.py",
                "src/{module}/infrastructure/messaging/handlers.py",
            ],
            "rust_structure": [
                "src/domain/mod.rs",
                "src/domain/models.rs",
                "src/domain/services.rs",
                "src/domain/ports/input.rs",
                "src/domain/ports/output.rs",
                "src/infrastructure/persistence/mod.rs",
                "src/infrastructure/persistence/repositories.rs",
                "src/infrastructure/web/mod.rs",
                "src/infrastructure/web/controllers.rs",
            ],
            "typescript_structure": [
                "src/domain/models.ts",
                "src/domain/services.ts",
                "src/domain/ports/input.ts",
                "src/domain/ports/output.ts",
                "src/infrastructure/persistence/repositories.ts",
                "src/infrastructure/web/controllers.ts",
            ],
        },
        "layered": {
            "description": "Layered Architecture - traditional N-tier separation",
            "python_structure": [
                "src/{module}/presentation/__init__.py",
                "src/{module}/presentation/api.py",
                "src/{module}/presentation/views.py",
                "src/{module}/business/__init__.py",
                "src/{module}/business/services.py",
                "src/{module}/business/models.py",
                "src/{module}/data/__init__.py",
                "src/{module}/data/repositories.py",
                "src/{module}/data/models.py",
            ],
            "rust_structure": [
                "src/presentation/api.rs",
                "src/presentation/views.rs",
                "src/business/services.rs",
                "src/business/models.rs",
                "src/data/repositories.rs",
                "src/data/models.rs",
            ],
            "typescript_structure": [
                "src/presentation/api.ts",
                "src/presentation/views.ts",
                "src/business/services.ts",
                "src/data/repositories.ts",
            ],
        },
        "microservices": {
            "description": "Microservices Architecture - independent services",
            "python_structure": [
                # Service template
                "services/{service_name}/src/__init__.py",
                "services/{service_name}/src/main.py",
                "services/{service_name}/src/api.py",
                "services/{service_name}/src/service.py",
                "services/{service_name}/tests/__init__.py",
                "services/{service_name}/tests/test_api.py",
                "services/{service_name}/pyproject.toml",
                "services/{service_name}/Dockerfile",
                # Shared
                "shared/events/__init__.py",
                "shared/events/base.py",
                "shared/types/__init__.py",
                # Infrastructure
                "api-gateway/src/main.py",
                "docker-compose.yml",
                "kubernetes/base/deployment.yaml",
            ],
            "rust_structure": [
                "services/{service_name}/src/main.rs",
                "services/{service_name}/src/lib.rs",
                "services/{service_name}/Cargo.toml",
                "services/{service_name}/Dockerfile",
                "shared/events/src/lib.rs",
                "api-gateway/src/main.rs",
                "docker-compose.yml",
            ],
            "typescript_structure": [
                "services/{service_name}/src/index.ts",
                "services/{service_name}/src/api.ts",
                "services/{service_name}/package.json",
                "services/{service_name}/tsconfig.json",
                "shared/events/index.ts",
                "api-gateway/src/index.ts",
                "docker-compose.yml",
            ],
        },
        "cqrs-es": {
            "description": "CQRS + Event Sourcing - separate reads/writes with audit trail",
            "python_structure": [
                "src/{module}/commands/__init__.py",
                "src/{module}/commands/handlers.py",
                "src/{module}/queries/__init__.py",
                "src/{module}/queries/handlers.py",
                "src/{module}/queries/projections.py",
                "src/{module}/events/__init__.py",
                "src/{module}/events/store.py",
                "src/{module}/aggregates/__init__.py",
                "src/{module}/aggregates/base.py",
            ],
            "rust_structure": [
                "src/commands/mod.rs",
                "src/commands/handlers.rs",
                "src/queries/mod.rs",
                "src/queries/handlers.rs",
                "src/queries/projections.rs",
                "src/events/mod.rs",
                "src/events/store.rs",
                "src/aggregates/mod.rs",
                "src/aggregates/base.rs",
            ],
            "typescript_structure": [
                "src/commands/handlers.ts",
                "src/queries/handlers.ts",
                "src/queries/projections.ts",
                "src/events/store.ts",
                "src/aggregates/base.ts",
            ],
        },
        "event-driven": {
            "description": "Event-Driven Architecture - asynchronous, decoupled communication",
            "python_structure": [
                "src/{module}/events/__init__.py",
                "src/{module}/events/publishers.py",
                "src/{module}/events/subscribers.py",
                "src/{module}/events/handlers/__init__.py",
                "src/{module}/processors/__init__.py",
                "src/{module}/sagas/__init__.py",
                "src/{module}/sagas/orchestrator.py",
            ],
            "rust_structure": [
                "src/events/mod.rs",
                "src/events/publishers.rs",
                "src/events/subscribers.rs",
                "src/events/handlers/mod.rs",
                "src/processors/mod.rs",
                "src/sagas/mod.rs",
                "src/sagas/orchestrator.rs",
            ],
            "typescript_structure": [
                "src/events/publishers.ts",
                "src/events/subscribers.ts",
                "src/events/handlers/index.ts",
                "src/processors/index.ts",
                "src/sagas/orchestrator.ts",
            ],
        },
        "pipeline": {
            "description": "Pipeline Architecture - processing stages for ETL/workflows",
            "python_structure": [
                "src/{module}/stages/__init__.py",
                "src/{module}/stages/extract.py",
                "src/{module}/stages/transform.py",
                "src/{module}/stages/load.py",
                "src/{module}/pipeline/__init__.py",
                "src/{module}/pipeline/orchestrator.py",
                "src/{module}/pipeline/config.py",
            ],
            "rust_structure": [
                "src/stages/extract.rs",
                "src/stages/transform.rs",
                "src/stages/load.rs",
                "src/pipeline/orchestrator.rs",
                "src/pipeline/config.rs",
            ],
            "typescript_structure": [
                "src/stages/extract.ts",
                "src/stages/transform.ts",
                "src/stages/load.ts",
                "src/pipeline/orchestrator.ts",
            ],
        },
        "modular-monolith": {
            "description": "Modular Monolith - single deployable with strong module boundaries",
            "python_structure": [
                "src/{module}/modules/__init__.py",
                "src/{module}/modules/users/__init__.py",
                "src/{module}/modules/users/api.py",
                "src/{module}/modules/users/domain.py",
                "src/{module}/modules/users/repository.py",
                "src/{module}/modules/orders/__init__.py",
                "src/{module}/modules/orders/api.py",
                "src/{module}/modules/orders/domain.py",
                "src/{module}/modules/orders/repository.py",
                "src/{module}/shared/__init__.py",
                "src/{module}/shared/events.py",
                "src/{module}/shared/interfaces.py",
                "src/{module}/api/__init__.py",
                "src/{module}/api/router.py",
            ],
            "rust_structure": [
                "src/modules/mod.rs",
                "src/modules/users/mod.rs",
                "src/modules/users/api.rs",
                "src/modules/users/domain.rs",
                "src/modules/users/repository.rs",
                "src/modules/orders/mod.rs",
                "src/modules/orders/api.rs",
                "src/modules/orders/domain.rs",
                "src/modules/orders/repository.rs",
                "src/shared/mod.rs",
                "src/shared/events.rs",
                "src/api/mod.rs",
                "src/api/router.rs",
            ],
            "typescript_structure": [
                "src/modules/users/api.ts",
                "src/modules/users/domain.ts",
                "src/modules/users/repository.ts",
                "src/modules/orders/api.ts",
                "src/modules/orders/domain.ts",
                "src/modules/orders/repository.ts",
                "src/shared/events.ts",
                "src/shared/interfaces.ts",
                "src/api/router.ts",
            ],
        },
        "service-based": {
            "description": "Service-Based Architecture - coarse-grained distributed services (SOA-lite)",
            "python_structure": [
                "services/user-service/src/__init__.py",
                "services/user-service/src/main.py",
                "services/user-service/src/service.py",
                "services/user-service/src/models.py",
                "services/order-service/src/__init__.py",
                "services/order-service/src/main.py",
                "services/order-service/src/service.py",
                "services/order-service/src/models.py",
                "shared/contracts/__init__.py",
                "shared/contracts/user.py",
                "shared/contracts/order.py",
                "gateway/src/main.py",
                "gateway/src/routes.py",
            ],
            "rust_structure": [
                "services/user-service/src/main.rs",
                "services/user-service/src/lib.rs",
                "services/user-service/src/service.rs",
                "services/order-service/src/main.rs",
                "services/order-service/src/lib.rs",
                "services/order-service/src/service.rs",
                "shared/contracts/src/lib.rs",
                "gateway/src/main.rs",
            ],
            "typescript_structure": [
                "services/user-service/src/index.ts",
                "services/user-service/src/service.ts",
                "services/order-service/src/index.ts",
                "services/order-service/src/service.ts",
                "shared/contracts/user.ts",
                "shared/contracts/order.ts",
                "gateway/src/index.ts",
            ],
        },
        "serverless": {
            "description": "Serverless Architecture - function-as-a-service with managed infrastructure",
            "python_structure": [
                "functions/create_user/__init__.py",
                "functions/create_user/handler.py",
                "functions/get_user/__init__.py",
                "functions/get_user/handler.py",
                "functions/process_order/__init__.py",
                "functions/process_order/handler.py",
                "shared/__init__.py",
                "shared/models.py",
                "shared/utils.py",
                "shared/database.py",
                "infrastructure/main.py",
                "infrastructure/resources.py",
                "serverless.yaml",
            ],
            "rust_structure": [
                "functions/create_user/src/main.rs",
                "functions/get_user/src/main.rs",
                "functions/process_order/src/main.rs",
                "shared/src/lib.rs",
                "shared/src/models.rs",
                "shared/src/database.rs",
                "infrastructure/main.rs",
            ],
            "typescript_structure": [
                "functions/create-user/handler.ts",
                "functions/get-user/handler.ts",
                "functions/process-order/handler.ts",
                "shared/models.ts",
                "shared/utils.ts",
                "shared/database.ts",
                "infrastructure/main.ts",
                "serverless.yml",
            ],
        },
        "space-based": {
            "description": "Space-Based Architecture - in-memory data grids for extreme scalability",
            "python_structure": [
                "src/{module}/spaces/__init__.py",
                "src/{module}/spaces/user_space.py",
                "src/{module}/spaces/order_space.py",
                "src/{module}/processing/__init__.py",
                "src/{module}/processing/user_processor.py",
                "src/{module}/processing/order_processor.py",
                "src/{module}/messaging/__init__.py",
                "src/{module}/messaging/grid.py",
                "src/{module}/messaging/replication.py",
                "src/{module}/api/__init__.py",
                "src/{module}/api/endpoints.py",
            ],
            "rust_structure": [
                "src/spaces/mod.rs",
                "src/spaces/user_space.rs",
                "src/spaces/order_space.rs",
                "src/processing/mod.rs",
                "src/processing/user_processor.rs",
                "src/processing/order_processor.rs",
                "src/messaging/mod.rs",
                "src/messaging/grid.rs",
                "src/messaging/replication.rs",
                "src/api/endpoints.rs",
            ],
            "typescript_structure": [
                "src/spaces/user-space.ts",
                "src/spaces/order-space.ts",
                "src/processing/user-processor.ts",
                "src/processing/order-processor.ts",
                "src/messaging/grid.ts",
                "src/messaging/replication.ts",
                "src/api/endpoints.ts",
            ],
        },
        "microkernel": {
            "description": "Microkernel Architecture - plugin-based extensible core system",
            "python_structure": [
                "src/{module}/core/__init__.py",
                "src/{module}/core/kernel.py",
                "src/{module}/core/plugin_manager.py",
                "src/{module}/core/registry.py",
                "src/{module}/plugins/__init__.py",
                "src/{module}/plugins/base.py",
                "src/{module}/plugins/example_plugin/__init__.py",
                "src/{module}/plugins/example_plugin/plugin.py",
                "src/{module}/api/__init__.py",
                "src/{module}/api/plugin_api.py",
                "src/{module}/api/core_api.py",
            ],
            "rust_structure": [
                "src/core/mod.rs",
                "src/core/kernel.rs",
                "src/core/plugin_manager.rs",
                "src/core/registry.rs",
                "src/plugins/mod.rs",
                "src/plugins/base.rs",
                "src/plugins/example_plugin/mod.rs",
                "src/plugins/example_plugin/plugin.rs",
                "src/api/plugin_api.rs",
                "src/api/core_api.rs",
            ],
            "typescript_structure": [
                "src/core/kernel.ts",
                "src/core/plugin-manager.ts",
                "src/core/registry.ts",
                "src/plugins/base.ts",
                "src/plugins/example-plugin/plugin.ts",
                "src/api/plugin-api.ts",
                "src/api/core-api.ts",
            ],
        },
        "client-server": {
            "description": "Client-Server Architecture - traditional centralized server with clients",
            "python_structure": [
                "server/src/__init__.py",
                "server/src/main.py",
                "server/src/handlers.py",
                "server/src/models.py",
                "server/src/database.py",
                "client/src/__init__.py",
                "client/src/main.py",
                "client/src/api_client.py",
                "client/src/ui.py",
                "shared/__init__.py",
                "shared/protocol.py",
                "shared/types.py",
            ],
            "rust_structure": [
                "server/src/main.rs",
                "server/src/handlers.rs",
                "server/src/models.rs",
                "server/src/database.rs",
                "client/src/main.rs",
                "client/src/api_client.rs",
                "client/src/ui.rs",
                "shared/src/lib.rs",
                "shared/src/protocol.rs",
            ],
            "typescript_structure": [
                "server/src/index.ts",
                "server/src/handlers.ts",
                "server/src/models.ts",
                "server/src/database.ts",
                "client/src/index.ts",
                "client/src/api-client.ts",
                "client/src/ui.ts",
                "shared/protocol.ts",
                "shared/types.ts",
            ],
        },
    }

    def __init__(
        self,
        paradigm: str,
        language: str,
        project_name: str,
        service_name: str = "service-a",
    ):
        """Initialize template customizer.

        Args:
            paradigm: Architecture paradigm name
            language: Programming language
            project_name: Name of the project
            service_name: Name for service templates (microservices, etc.)

        """
        self.paradigm = paradigm
        self.language = language
        self.project_name = project_name
        self.module_name = project_name.replace("-", "_")
        self.service_name = service_name

    def get_structure(self) -> list[str]:
        """Get directory structure for the paradigm and language.

        Returns:
            List of directory/file paths to create

        """
        if self.paradigm not in self.STRUCTURE_TEMPLATES:
            print(f"Warning: No specific structure for {self.paradigm}, using layered")
            self.paradigm = "layered"

        paradigm_config = self.STRUCTURE_TEMPLATES[self.paradigm]
        structure_key = f"{self.language}_structure"

        if structure_key not in paradigm_config:
            raise ValueError(f"Unsupported language: {self.language}")

        raw_structure = paradigm_config[structure_key]

        # Replace placeholders
        return [
            path.replace("{module}", self.module_name).replace(
                "{service_name}", self.service_name
            )
            for path in raw_structure
        ]

    def get_paradigm_description(self) -> str:
        """Get description of the selected paradigm.

        Returns:
            Paradigm description string

        """
        if self.paradigm in self.STRUCTURE_TEMPLATES:
            return self.STRUCTURE_TEMPLATES[self.paradigm]["description"]
        return "Standard project structure"

    def generate_architecture_readme(self) -> str:
        """Generate README section explaining the architecture.

        Returns:
            Markdown string with architecture documentation

        """
        description = self.get_paradigm_description()

        readme_content = f"""# Architecture

This project uses **{self.paradigm.replace('-', ' ').title()} Architecture**.

## Overview

{description}

## Structure

"""
        structure = self.get_structure()
        for path in structure:
            readme_content += f"- `{path}`\n"

        readme_content += f"""

## Implementation

For detailed implementation guidance, see:
```bash
Skill(architecture-paradigm-{self.paradigm})
```

## Key Principles

1. **Separation of Concerns**: Clear boundaries between layers/components
2. **Testability**: Architecture enables comprehensive testing
3. **Maintainability**: Structure supports evolution and growth
4. **Documentation**: Keep architectural decisions documented

## Evolution

As the project grows, consider:
- Monitoring architecture metrics
- Periodic architecture reviews
- Evolution patterns to next paradigm if needed
"""

        return readme_content

    def create_architecture_directories(self, project_path: Path) -> list[str]:
        """Create directory structure for the paradigm.

        Args:
            project_path: Root path of the project

        Returns:
            List of created directories

        """
        structure = self.get_structure()
        created_dirs = []

        for path_str in structure:
            # Create directory for each file path
            path_obj = project_path / path_str
            parent_dir = path_obj.parent

            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(parent_dir))

        return created_dirs

    def generate_architecture_adr(self) -> str:
        """Generate Architecture Decision Record.

        Returns:
            ADR content as string

        """
        return f"""# Architecture Decision Record: {self.paradigm.replace('-', ' ').title()}

## Date
{self._get_current_date()}

## Status
Accepted

## Context
This project required an architecture that supports:
- Team size and structure
- Domain complexity
- Technology choices
- Scalability and performance requirements

## Decision
Adopted **{self.paradigm.replace('-', ' ').title()} Architecture**.

## Rationale
{self.get_paradigm_description()}

### Key Benefits
- Clear separation of concerns
- Improved testability
- Better maintainability
- Support for team growth

### Trade-offs
- [Paradigm-specific trade-offs documented in paradigm skill]

## Implementation
- **Structure**: See ARCHITECTURE.md for detailed structure
- **Patterns**: Follow guidance in `Skill(architecture-paradigm-{self.paradigm})`
- **Examples**: Refer to paradigm skill for case studies

## Consequences
### Positive
- Architecture supports current and future needs
- Clear boundaries enable independent testing and evolution
- Team can work autonomously within boundaries

### Negative
- [Potential downsides and mitigations]

## References
- Paradigm skill: `Skill(architecture-paradigm-{self.paradigm})`
- Architecture documentation: ARCHITECTURE.md
"""

    def _get_current_date(self) -> str:
        """Get current date in ISO format.

        Returns:
            Date string

        """
        return datetime.now().strftime("%Y-%m-%d")


def main():
    """CLI entry point for template customizer."""
    parser = argparse.ArgumentParser(
        description="Generate architecture-specific project structure"
    )
    parser.add_argument(
        "--paradigm",
        required=True,
        choices=[
            "layered",
            "hexagonal",
            "functional-core",
            "modular-monolith",
            "microservices",
            "service-based",
            "event-driven",
            "cqrs-es",
            "serverless",
            "space-based",
            "pipeline",
            "microkernel",
            "client-server",
        ],
        help="Architecture paradigm to use",
    )
    parser.add_argument(
        "--language",
        required=True,
        choices=["python", "rust", "typescript"],
        help="Programming language",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for project structure (creates directories if provided)",
    )
    parser.add_argument(
        "--generate-adr",
        action="store_true",
        help="Generate Architecture Decision Record",
    )
    parser.add_argument(
        "--generate-readme",
        action="store_true",
        help="Generate ARCHITECTURE.md",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list structure, don't create files",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output structure as JSON",
    )

    args = parser.parse_args()

    customizer = TemplateCustomizer(args.paradigm, args.language, args.project_name)

    if args.output_json:
        output = {
            "paradigm": args.paradigm,
            "description": customizer.get_paradigm_description(),
            "language": args.language,
            "project_name": args.project_name,
            "structure": customizer.get_structure(),
        }
        print(json.dumps(output, indent=2))
        return

    print("=" * 60)
    print("Template Customization")
    print("=" * 60)
    print(f"\nParadigm: {args.paradigm}")
    print(f"Description: {customizer.get_paradigm_description()}")
    print(f"Language: {args.language}")
    print(f"Project: {args.project_name}")
    print("\nDirectory Structure:")
    print("-" * 60)
    for path in customizer.get_structure():
        print(f"  {path}")

    if args.output_dir and not args.list_only:
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nCreating directories in: {output_path}")
        created = customizer.create_architecture_directories(output_path)
        print(f"Created {len(created)} directories")

        if args.generate_readme:
            readme_path = output_path / "ARCHITECTURE.md"
            readme_path.write_text(customizer.generate_architecture_readme())
            print(f"Created: {readme_path}")

        if args.generate_adr:
            adr_dir = output_path / "docs" / "adr"
            adr_dir.mkdir(parents=True, exist_ok=True)
            adr_path = adr_dir / "001-architecture-paradigm.md"
            adr_path.write_text(customizer.generate_architecture_adr())
            print(f"Created: {adr_path}")

    if args.generate_adr and args.list_only:
        print("\n" + "=" * 60)
        print("Architecture Decision Record")
        print("=" * 60)
        print(customizer.generate_architecture_adr())

    if args.generate_readme and args.list_only:
        print("\n" + "=" * 60)
        print("ARCHITECTURE.md")
        print("=" * 60)
        print(customizer.generate_architecture_readme())


if __name__ == "__main__":
    main()
