#!/usr/bin/env python3
"""Centralized configuration management for Abstract tools and skills.

Consolidates all configuration values and provides validation.
"""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    pass


class Environment(Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class SkillValidationConfig:
    """Configuration for skill validation."""

    # Skills exempt from meta-skill indicator requirements
    META_SKILL_EXCEPTIONS: list[str] | None = None

    # Meta-skill indicators
    META_INDICATORS: list[str] | None = None

    # Required frontmatter fields
    REQUIRED_FRONTMATTER_FIELDS: list[str] | None = None

    # Recommended frontmatter fields
    RECOMMENDED_FRONTMATTER_FIELDS: list[str] | None = None

    # File size limits
    MAX_SKILL_FILE_SIZE: int = 15000  # bytes
    MAX_TOTAL_SKILL_SIZE: int = 100000  # bytes

    def __post_init__(self) -> None:
        """Initialize default values for None fields."""
        if self.META_SKILL_EXCEPTIONS is None:
            self.META_SKILL_EXCEPTIONS = [
                "skills-eval",
                "modular-skills",
                "writing-clearly-and-concisely",
            ]

        if self.META_INDICATORS is None:
            self.META_INDICATORS = [
                "pattern",
                "template",
                "framework",
                "infrastructure",
                "meta-skill",
                "orchestrat",
                "design pattern",
                "methodology",
            ]

        if self.REQUIRED_FRONTMATTER_FIELDS is None:
            self.REQUIRED_FRONTMATTER_FIELDS = ["name", "description"]

        if self.RECOMMENDED_FRONTMATTER_FIELDS is None:
            self.RECOMMENDED_FRONTMATTER_FIELDS = [
                "category",
                "tags",
                "dependencies",
                "tools",
                "usage_patterns",
                "complexity",
                "estimated_tokens",
            ]


@dataclass
class SkillAnalyzerConfig:
    """Configuration for skill analyzer tool."""

    DEFAULT_THRESHOLD: int = 150  # lines
    MIN_THRESHOLD: int = 1
    MAX_THRESHOLD: int = 10000
    TOKEN_RATIO: int = 4  # characters per token

    # Warning thresholds
    LARGE_FILE_LINES: int = 200
    MANY_THEMES: int = 3
    MANY_CODE_BLOCKS: int = 3

    # File extensions to analyze
    MARKDOWN_EXTENSIONS: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize default values for None fields."""
        if self.MARKDOWN_EXTENSIONS is None:
            self.MARKDOWN_EXTENSIONS = [".md", ".markdown"]


@dataclass
class SkillsEvalConfig:
    """Configuration for skills evaluation."""

    # Scoring weights
    STRUCTURE_WEIGHT: float = 0.20
    CONTENT_WEIGHT: float = 0.20
    TOKEN_WEIGHT: float = 0.15
    ACTIVATION_WEIGHT: float = 0.20
    TOOL_WEIGHT: float = 0.15
    DOCUMENTATION_WEIGHT: float = 0.10

    # Score thresholds
    MINIMUM_QUALITY_THRESHOLD: float = 70.0
    HIGH_QUALITY_THRESHOLD: float = 80.0
    EXCELLENT_QUALITY_THRESHOLD: float = 90.0

    # Token efficiency ranges
    OPTIMAL_TOKEN_RANGE: tuple = (800, 2000)
    ACCEPTABLE_TOKEN_RANGE: tuple = (2000, 3000)

    # Search paths for skills
    CLAUDE_PATHS: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize default values for None fields."""
        if self.CLAUDE_PATHS is None:
            home = Path.home()
            self.CLAUDE_PATHS = [
                str(home / ".claude"),
                str(home / ".claude" / "superpowers" / "skills"),
                str(home / ".claude" / "skills"),
            ]


@dataclass
class ContextOptimizerConfig:
    """Configuration for context optimization."""

    # Progressive disclosure thresholds
    PROGRESSIVE_DISCLOSURE_THRESHOLDS: dict[str, int] | None = None

    # Size categories
    SMALL_SIZE_LIMIT: int = 2000
    MEDIUM_SIZE_LIMIT: int = 5000
    LARGE_SIZE_LIMIT: int = 15000

    # Content optimization
    MAX_SECTION_LINES: int = 20
    MAX_LINE_LENGTH: int = 100
    TARGET_TOKENS_PER_SECTION: int = 200

    def __post_init__(self) -> None:
        """Initialize progressive disclosure thresholds if not set."""
        if self.PROGRESSIVE_DISCLOSURE_THRESHOLDS is None:
            self.PROGRESSIVE_DISCLOSURE_THRESHOLDS = {
                "small": self.SMALL_SIZE_LIMIT,
                "medium": self.MEDIUM_SIZE_LIMIT,
                "large": self.LARGE_SIZE_LIMIT,
            }


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling."""

    # Error severity levels
    EXIT_CODES: dict[str, int] | None = None

    # Default log levels
    DEFAULT_LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Error reporting
    MAX_ERROR_CONTEXT_LINES: int = 5
    ERROR_CACHE_SIZE: int = 100

    def __post_init__(self) -> None:
        """Initialize exit codes if not set."""
        if self.EXIT_CODES is None:
            self.EXIT_CODES = {
                "SUCCESS": 0,
                "GENERAL_ERROR": 1,
                "ARGUMENT_ERROR": 2,
                "FILE_NOT_FOUND": 3,
                "PERMISSION_ERROR": 4,
                "VALIDATION_ERROR": 5,
                "CONFIGURATION_ERROR": 6,
            }


@dataclass
class AbstractConfig:
    """Main configuration container."""

    # Configuration validation tolerance
    FLOAT_POINT_TOLERANCE = 0.01

    environment: Environment = Environment.PRODUCTION

    # Sub-configurations
    skill_validation: SkillValidationConfig | None = None
    skill_analyzer: SkillAnalyzerConfig | None = None
    skills_eval: SkillsEvalConfig | None = None
    context_optimizer: ContextOptimizerConfig | None = None
    error_handling: ErrorHandlingConfig | None = None

    # Global settings
    debug: bool = False
    verbose: bool = False
    log_file: str | None = None

    # Paths
    project_root: str | None = None
    config_dir: str = "config"
    scripts_dir: str = "scripts"

    def __post_init__(self) -> None:
        """Initialize sub-configurations with defaults."""
        # Initialize sub-configurations with defaults
        if self.skill_validation is None:
            self.skill_validation = SkillValidationConfig()
        if self.skill_analyzer is None:
            self.skill_analyzer = SkillAnalyzerConfig()
        if self.skills_eval is None:
            self.skills_eval = SkillsEvalConfig()
        if self.context_optimizer is None:
            self.context_optimizer = ContextOptimizerConfig()
        if self.error_handling is None:
            self.error_handling = ErrorHandlingConfig()

        # Set project root if not specified
        if self.project_root is None:
            self.project_root = str(Path.cwd())

    @classmethod
    def from_file(cls, config_path: str | Path) -> "AbstractConfig":
        """Load configuration from file."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Determine file format
        if config_path.suffix.lower() in [".yaml", ".yml"]:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
        elif config_path.suffix.lower() == ".json":
            with open(config_path) as f:
                config_data = json.load(f)
        else:
            raise ValueError(
                f"Unsupported configuration file format: {config_path.suffix}"
            )

        # Convert nested dicts to configuration objects
        if "skill_validation" in config_data:
            config_data["skill_validation"] = SkillValidationConfig(
                **config_data["skill_validation"]
            )

        if "skill_analyzer" in config_data:
            config_data["skill_analyzer"] = SkillAnalyzerConfig(
                **config_data["skill_analyzer"]
            )

        if "skills_eval" in config_data:
            config_data["skills_eval"] = SkillsEvalConfig(**config_data["skills_eval"])

        if "context_optimizer" in config_data:
            config_data["context_optimizer"] = ContextOptimizerConfig(
                **config_data["context_optimizer"]
            )

        if "error_handling" in config_data:
            config_data["error_handling"] = ErrorHandlingConfig(
                **config_data["error_handling"]
            )

        return cls(**config_data)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "AbstractConfig":
        """Load configuration from YAML file (most common format)."""
        return cls.from_file(yaml_path)

    @classmethod
    def from_env(cls) -> "AbstractConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Environment override for debug/verbose
        config.debug = os.getenv("ABSTRACT_DEBUG", "").lower() in ("true", "1", "yes")
        config.verbose = os.getenv("ABSTRACT_VERBOSE", "").lower() in (
            "true",
            "1",
            "yes",
        )
        config.log_file = os.getenv("ABSTRACT_LOG_FILE")

        # Environment override for environment type
        env_str = os.getenv("ABSTRACT_ENV", "production").lower()
        try:
            config.environment = Environment(env_str)
        except ValueError:
            config.environment = Environment.PRODUCTION

        return config

    def to_file(self, config_path: str | Path, fmt: str = "yaml") -> None:
        """Save configuration to file."""
        config_path = Path(config_path)

        # Convert to dictionary
        config_dict = asdict(self)

        # Convert enum to string
        if "environment" in config_dict:
            config_dict["environment"] = config_dict["environment"].value

        # Create directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save based on format
        if fmt.lower() in ["yaml", "yml"]:
            with open(config_path, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        elif fmt.lower() == "json":
            with open(config_path, "w") as f:
                json.dump(config_dict, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def get_path(self, path_key: str) -> str:
        """Get a resolved path."""
        if self.project_root is None:
            raise ValueError("project_root is not set")
        base_path = Path(self.project_root)

        if path_key == "config_dir":
            return str(base_path / self.config_dir)
        elif path_key == "scripts_dir":
            return str(base_path / self.scripts_dir)
        elif path_key == "project_root":
            return self.project_root
        else:
            raise ValueError(f"Unknown path key: {path_key}")

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Validate numeric ranges (ensure sub-configs exist)
        if self.skill_analyzer is not None:
            default = self.skill_analyzer.DEFAULT_THRESHOLD
            min_thresh = self.skill_analyzer.MIN_THRESHOLD
            if default < min_thresh:
                issues.append(
                    f"Threshold {self.skill_analyzer.DEFAULT_THRESHOLD} "
                    f"below minimum {self.skill_analyzer.MIN_THRESHOLD}"
                )

            max_thresh = self.skill_analyzer.MAX_THRESHOLD
            if default > max_thresh:
                issues.append(
                    f"Threshold {default} above maximum {max_thresh}"
                )

        # Validate weights sum to 1.0
        if self.skills_eval is not None:
            total_weight = (
                self.skills_eval.STRUCTURE_WEIGHT
                + self.skills_eval.CONTENT_WEIGHT
                + self.skills_eval.TOKEN_WEIGHT
                + self.skills_eval.ACTIVATION_WEIGHT
                + self.skills_eval.TOOL_WEIGHT
                + self.skills_eval.DOCUMENTATION_WEIGHT
            )

            if abs(total_weight - 1.0) > self.FLOAT_POINT_TOLERANCE:
                # Allow small floating point errors
                issues.append(f"Scoring weights sum to {total_weight}, should be 1.0")

        # Validate paths exist
        if self.project_root is not None and not Path(self.project_root).exists():
            issues.append(f"Project root does not exist: {self.project_root}")

        return issues

    def get_summary(self) -> str:
        """Get configuration summary."""
        # Ensure sub-configs are initialized (they should be after __post_init__)
        if self.skill_validation is None:
            raise ValueError("skill_validation not initialized")
        if self.skill_analyzer is None:
            raise ValueError("skill_analyzer not initialized")
        if self.skills_eval is None:
            raise ValueError("skills_eval not initialized")
        if self.context_optimizer is None:
            raise ValueError("context_optimizer not initialized")

        # Get exception count safely
        exception_count = (
            len(self.skill_validation.META_SKILL_EXCEPTIONS)
            if self.skill_validation.META_SKILL_EXCEPTIONS
            else 0
        )

        lines = [
            "Abstract Configuration Summary",
            "=" * 30,
            f"Environment: {self.environment.value}",
            f"Debug: {self.debug}",
            f"Verbose: {self.verbose}",
            f"Project Root: {self.project_root}",
            "",
            "Skill Validation:",
            f"  Max File Size: {self.skill_validation.MAX_SKILL_FILE_SIZE:,} bytes",
            f"  Exceptions: {exception_count} skills",
            "",
            "Skill Analyzer:",
            f"  Default Threshold: {self.skill_analyzer.DEFAULT_THRESHOLD} lines",
            f"  Token Ratio: 1:{self.skill_analyzer.TOKEN_RATIO}",
            "",
            "Skills Evaluation:",
            f"  Quality Threshold: {self.skills_eval.MINIMUM_QUALITY_THRESHOLD}",
            f"  Optimal Token Range: {self.skills_eval.OPTIMAL_TOKEN_RANGE}",
            "",
            "Context Optimizer:",
            f"  Small Files: <{self.context_optimizer.SMALL_SIZE_LIMIT:,} bytes",
            f"  Medium Files: <{self.context_optimizer.MEDIUM_SIZE_LIMIT:,} bytes",
        ]

        return "\n".join(lines)


class ConfigFactory:
    """Factory for creating and managing configuration instances."""

    _instances: dict[str, AbstractConfig] = {}

    @classmethod
    def get_config(cls, name: str = "default") -> AbstractConfig:
        """Get configuration instance by name."""
        if name not in cls._instances:
            # Try to load from config file
            config_file = Path.cwd() / "config" / "abstract_config.yaml"
            if config_file.exists():
                cls._instances[name] = AbstractConfig.from_file(config_file)
            else:
                # Fall back to environment variables and defaults
                cls._instances[name] = AbstractConfig.from_env()

        return cls._instances[name]

    @classmethod
    def set_config(cls, config: AbstractConfig, name: str = "default") -> None:
        """Set configuration instance by name."""
        cls._instances[name] = config

    @classmethod
    def reset_config(cls, name: str = "default") -> None:
        """Reset configuration instance by name."""
        if name in cls._instances:
            del cls._instances[name]

    @classmethod
    def create_config(cls, **kwargs: Any) -> AbstractConfig:
        """Create a new configuration with custom parameters."""
        return AbstractConfig(**kwargs)

    @classmethod
    def load_config(
        cls, config_path: str | Path, name: str = "default"
    ) -> AbstractConfig:
        """Load configuration from file and store with given name."""
        config = AbstractConfig.from_file(config_path)
        cls.set_config(config, name)
        return config
