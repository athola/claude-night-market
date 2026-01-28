#!/usr/bin/env python3
"""Tool: Quick Start Generator.

Description: Automated quick-start generator for existing skills. Creates
lightweight variants focused on essential information.

Usage: scripts/quick_start_generator.py [--skill-path PATH] [--output PATH]
[--template TEMPLATE].
"""

import argparse
import logging
import re
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class QuickStartGenerator:
    """Generates quick-start variants of skills with essential information only."""

    def __init__(self, skill_path: str) -> None:
        """Initialize quick start generator.

        Args:
            skill_path: Path to the skill file to process.

        """
        self.skill_path = Path(skill_path)
        self.skill_dir = self.skill_path.parent
        self.skill_content = self._load_skill_content()
        self.frontmatter, self.content = self._parse_skill_content()

    def _load_skill_content(self) -> list[str]:
        """Load skill content as lines."""
        try:
            with open(self.skill_path, encoding="utf-8") as f:
                return f.readlines()
        except FileNotFoundError as err:
            msg = f"Skill file not found: {self.skill_path}"
            raise FileNotFoundError(msg) from err

    def _parse_skill_content(self) -> tuple[dict, list[str]]:
        """Parse YAML frontmatter and content."""
        content_lines = self.skill_content

        if not content_lines or not content_lines[0].strip().startswith("---"):
            return {}, content_lines

        frontmatter_end = None
        for i, line in enumerate(content_lines[1:], 1):
            if line.strip() == "---":
                frontmatter_end = i
                break

        if frontmatter_end is None:
            return {}, content_lines

        try:
            frontmatter_text = "".join(content_lines[1:frontmatter_end])
            frontmatter = yaml.safe_load(frontmatter_text) or {}
            content = content_lines[frontmatter_end + 1 :]
            return frontmatter, content
        except yaml.YAMLError:
            return {}, content_lines

    def generate_quick_start(self) -> str:
        """Generate quick-start content focusing on essential information."""
        quick_start_lines = []

        # Add optimized frontmatter
        quick_start_lines.extend(self._generate_quick_start_frontmatter())

        # Add title
        if self.content:
            quick_start_lines.append("\n")
            # Find first # heading
            for line in self.content:
                if line.strip().startswith("#"):
                    title = line.strip() + " (Quick Start)\n"
                    quick_start_lines.append(title)
                    break

        # Add purpose section
        quick_start_lines.extend(self._extract_purpose_section())

        # Add when to use
        quick_start_lines.extend(self._extract_when_to_use())

        # Add quick usage examples
        quick_start_lines.extend(self._extract_quick_usage())

        # Add essential tools
        quick_start_lines.extend(self._extract_essential_tools())

        # Add key benefits (brief)
        quick_start_lines.extend(self._extract_key_benefits())

        # Add loading marker for full content
        quick_start_lines.append("\n<!-- FULL_CONTENT_AVAILABLE -->\n")
        quick_start_lines.append(
            "<!-- Implementation details, examples, and workflows "
            "available in full SKILL.md -->\n",
        )

        # Add optional quick implementation steps
        quick_start_lines.extend(self._extract_quick_implementation())

        return "".join(quick_start_lines)

    def _generate_quick_start_frontmatter(self) -> list[str]:
        """Generate optimized frontmatter for quick-start."""
        quick_frontmatter = dict(self.frontmatter)

        # Optimize for quick usage
        quick_frontmatter.update(
            {
                "estimated_tokens": min(
                    quick_frontmatter.get("estimated_tokens", 800),
                    300,
                ),
                "complexity": quick_frontmatter.get("complexity", "intermediate"),
                "description": (
                    f"{quick_frontmatter.get('description', '')} (Quick Start)"
                ),
            },
        )

        # Add tools only if they exist
        if "tools" not in quick_frontmatter and self.frontmatter:
            quick_frontmatter["tools"] = self.frontmatter.get("tools", [])

        frontmatter_lines = ["---\n"]
        for key, value in quick_frontmatter.items():
            frontmatter_lines.append(f"{key}: {value}\n")
        frontmatter_lines.append("---\n")

        return frontmatter_lines

    def _extract_purpose_section(self) -> list[str]:
        """Extract or create a concise purpose section."""
        purpose_lines = ["\n## Purpose\n"]

        # Look for existing purpose/overview section
        content_text = "".join(self.content)

        # Try to find existing purpose/overview
        purpose_patterns = [
            r"##\s*(?:Purpose|Overview|What.*Is)\s*\n(.*?)(?=\n##|\n\n)",
            r"###?\s*(?:Purpose|Overview)\s*\n(.*?)(?=\n#|\n\n)",
        ]

        for pattern in purpose_patterns:
            match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
            if match:
                purpose_text = match.group(1).strip()
                # Shorten to 1-2 sentences
                sentences = re.split(r"[.!?]+", purpose_text)
                if sentences:
                    short_purpose = ". ".join(sentences[:2]).strip()
                    if short_purpose and not short_purpose.endswith("."):
                        short_purpose += "."
                    purpose_lines.append(f"{short_purpose}\n")
                    return purpose_lines

        # Generate default purpose from description
        if self.frontmatter and "description" in self.frontmatter:
            description = self.frontmatter["description"]
            # Extract first sentence
            first_sentence = re.split(r"[.!?]+", description)[0]
            purpose_lines.append(f"{first_sentence}.\n")
        else:
            purpose_lines.append(
                "Essential skill functionality for specific use cases.\n",
            )

        return purpose_lines

    def _extract_when_to_use(self) -> list[str]:
        """Extract concise when to use section."""
        when_to_use_lines = ["\n## When to Use\n"]

        content_text = "".join(self.content)

        # Look for existing when to use section
        when_patterns = [
            r"##\s*(?:When to Use|Use Cases|Perfect for)\s*\n(.*?)(?=\n##|\n\n)",
            r"###?\s*(?:When to Use|Use Cases)\s*\n(.*?)(?=\n#|\n\n)",
        ]

        for pattern in when_patterns:
            match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
            if match:
                use_text = match.group(1).strip()
                # Extract bullet points or create them
                bullets = re.findall(r"[OK-]\s*(.*?)(?=\n|$)", use_text)
                if bullets:
                    for bullet in bullets[:4]:  # Limit to 4 key points
                        cleaned_bullet = re.sub(r"\s+", " ", bullet.strip())
                        if cleaned_bullet:
                            prefix = (
                                "" if not cleaned_bullet.startswith(("", "")) else ""
                            )
                            when_to_use_lines.append(f"{prefix} {cleaned_bullet}\n")
                    return when_to_use_lines

        # Generate generic when to use
        when_to_use_lines.append(" Common use cases and scenarios\n")
        when_to_use_lines.append(" Not suitable for alternative approaches\n")

        return when_to_use_lines

    def _extract_quick_usage(self) -> list[str]:
        """Extract quick usage examples."""
        usage_lines = ["\n## Quick Usage\n"]

        content_text = "".join(self.content)

        # Look for existing quick start or usage sections
        usage_patterns = [
            r"##\s*(?:Quick Start|Usage|Quick Usage|Getting Started)\s*\n"
            r"(.*?)(?=\n##|\n\n)",
            r"```bash\s*\n(.*?)(?=```)",
            r"```python\s*\n(.*?)(?=```)",
        ]

        for pattern in usage_patterns:
            matches = re.findall(pattern, content_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Limit to 3 examples
                    usage_text = match.strip()
                    if usage_text:
                        usage_lines.append(f"```bash\n{usage_text}\n```\n")
                return usage_lines

        # Check for tools in frontmatter
        if self.frontmatter and "tools" in self.frontmatter:
            tools = self.frontmatter["tools"]
            if isinstance(tools, list) and tools:
                usage_lines.append("```bash\n# Available tools\n")
                for tool in tools[:3]:  # Show first 3 tools
                    if isinstance(tool, str):
                        usage_lines.append(f"# {tool}\n")
                usage_lines.append("```\n")

        return usage_lines

    def _extract_essential_tools(self) -> list[str]:
        """Extract essential tools information."""
        tools_lines = ["\n## Essential Tools\n"]

        if self.frontmatter and "tools" in self.frontmatter:
            tools = self.frontmatter["tools"]
            if isinstance(tools, list) and tools:
                for tool in tools[:4]:  # Limit to 4 essential tools
                    if isinstance(tool, str):
                        tool_desc = self._get_tool_description(tool)
                        tools_lines.append(f"- `{tool}`: {tool_desc}\n")
                    elif isinstance(tool, dict) and "name" in tool:
                        name = tool["name"]
                        desc = tool.get("description", "Essential tool functionality")
                        tools_lines.append(f"- `{name}`: {desc}\n")
        else:
            tools_lines.append("- Essential tools for skill functionality\n")

        return tools_lines

    def _get_tool_description(self, tool_name: str) -> str:
        """Get description for a tool name."""
        # Look for tool descriptions in content
        content_text = "".join(self.content)

        tool_pattern = (
            rf"(?:{re.escape(tool_name)}.*?)(?:-|:)\s*([^.!?\n]*[.!?]?)(?=\n|$)"
        )
        match = re.search(tool_pattern, content_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Generate generic descriptions
        generic_descriptions = {
            "skill-analyzer": "Complexity analysis and recommendations",
            "token-estimator": "Usage forecasting and optimization",
            "module_validator": "Structure validation and compliance",
            "skills-auditor": "detailed skill discovery and analysis",
            "improvement-suggester": "Prioritized improvement recommendations",
            "compliance-checker": "Standards validation and security checking",
        }

        return generic_descriptions.get(tool_name, "Essential tool functionality")

    def _extract_key_benefits(self) -> list[str]:
        """Extract key benefits section."""
        benefits_lines = ["\n## Key Benefits\n"]

        # Look for benefits section in content
        content_text = "".join(self.content)

        benefits_patterns = [
            r"##\s*(?:Key Benefits|Benefits|Advantages)\s*\n(.*?)(?=\n##|\n\n)",
            r"###?\s*(?:Key Benefits|Benefits)\s*\n(.*?)(?=\n#|\n\n)",
        ]

        for pattern in benefits_patterns:
            match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
            if match:
                benefits_text = match.group(1).strip()
                # Extract bullet points
                bullets = re.findall(
                    r"[*-]\s*\*\*(.*?)\*\*:\s*(.*?)(?=\n|$)",
                    benefits_text,
                )
                if bullets:
                    for benefit, desc in bullets[:3]:  # Limit to 3 benefits
                        benefits_lines.append(
                            f"- **{benefit.strip()}**: {desc.strip()}\n",
                        )
                    return benefits_lines

        # Generate generic benefits
        benefits_lines.extend(
            [
                "- **Quality Assurance**: Systematic evaluation against standards\n",
                "- **Performance Optimization**: Token usage analysis and "
                "recommendations\n",
                "- **Maintainability**: Clear structure for easier management\n",
            ],
        )

        return benefits_lines

    def _extract_quick_implementation(self) -> list[str]:
        """Extract quick implementation steps."""
        impl_lines = ["\n## Quick Implementation\n"]

        content_text = "".join(self.content)

        # Look for workflow or implementation steps
        workflow_patterns = [
            r"##\s*(?:Implementation|Workflow|Quick Implementation)\s*\n"
            r"(.*?)(?=\n##|\n\n)",
            r"###?\s*(?:Implementation|Workflow)\s*\n(.*?)(?=\n#|\n\n)",
        ]

        for pattern in workflow_patterns:
            match = re.search(pattern, content_text, re.DOTALL | re.IGNORECASE)
            if match:
                workflow_text = match.group(1).strip()
                # Extract numbered steps
                steps = re.findall(r"\d+\.\s*(.*?)(?=\n\d+\.|\n\n|\n#)", workflow_text)
                if steps:
                    for step in steps[:4]:  # Limit to 4 steps
                        impl_lines.append(f"{len(impl_lines)}. {step.strip()}\n")
                    return impl_lines

        # Generate generic steps
        impl_lines.extend(
            [
                "1. **Assess**: Analyze current skill structure and complexity\n",
                "2. **Design**: Plan modular architecture based on single "
                "responsibility\n",
                "3. **Validate**: Run quality checks and compliance validation\n",
            ],
        )

        return impl_lines

    def save_quick_start(self, output_path: str | None = None) -> str:
        """Save quick-start variant."""
        if output_path is None:
            output_path = self.skill_dir / "QUICK_START.md"

        quick_start_content = self.generate_quick_start()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(quick_start_content)

        return str(output_path)


def _process_batch_directory(batch_path: str, show_stats: bool) -> None:
    """Process all SKILL.md files in a directory."""
    batch_dir = Path(batch_path)
    if not batch_dir.exists():
        msg = f"Directory not found: {batch_path}"
        raise FileNotFoundError(msg)

    skill_files = list(batch_dir.glob("**/SKILL.md"))
    if not skill_files:
        sys.exit(1)

    generated_count = 0
    total_tokens_saved = 0

    for skill_file in skill_files:
        try:
            generator = QuickStartGenerator(str(skill_file))
            output_path = generator.save_quick_start()
            generated_count += 1

            # Calculate estimated savings
            original_size = skill_file.stat().st_size
            quick_size = Path(output_path).stat().st_size
            tokens_saved = (original_size - quick_size) // 4
            total_tokens_saved += tokens_saved

        except Exception as e:
            logger.debug(f"Failed to process {output_path}: {e}")

    if show_stats:
        total_tokens_saved // generated_count


def _process_single_skill(
    skill_path: str,
    output_path: str | None,
    show_stats: bool,
) -> None:
    """Process a single skill file."""
    generator = QuickStartGenerator(skill_path)
    output = generator.save_quick_start(output_path)

    if show_stats:
        original_size = Path(skill_path).stat().st_size
        quick_size = Path(output).stat().st_size
        (original_size - quick_size) // 4


def main() -> None:
    """Generate quick-start variants of skills."""
    parser = argparse.ArgumentParser(
        description="Generate quick-start variants of skills",
    )
    parser.add_argument("skill_path", help="Path to skill file")
    parser.add_argument("--output", help="Output path for quick-start variant")
    parser.add_argument("--batch", help="Process all skills in directory")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show generation statistics",
    )

    args = parser.parse_args()

    try:
        if args.batch:
            _process_batch_directory(args.batch, args.stats)
        else:
            _process_single_skill(args.skill_path, args.output, args.stats)

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
