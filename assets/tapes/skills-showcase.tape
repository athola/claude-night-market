# @title: Skills Showcase
# @description: Demonstrate skill discovery, validation, and execution in Claude Code workflows

Output assets/gifs/skills-showcase.gif

Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# @step Discover Skills in the Project
# @docs-brief List all available skills across plugins
# @book-detail The claude-night-market contains 100+ skills across 14 plugins. Skills are the building blocks of workflows - reusable, composable units that Claude Code can invoke. Let's explore what's available.

Type "# First, see what skills are available in the abstract plugin"
Enter
Sleep 500ms

Type "ls plugins/abstract/skills/"
Enter
Sleep 2s

Type "clear"
Enter
Sleep 500ms

# @step Count Total Skills Across All Plugins
# @docs-brief Get a quick count of total skills in the project
# @book-detail Each plugin organizes its skills in a 'skills/' directory. Each skill has a SKILL.md file that defines its behavior, dependencies, and usage patterns.

Type "# Count all skills across the entire marketplace"
Enter
Sleep 500ms

Type "find plugins -name 'SKILL.md' -type f | wc -l"
Enter
Sleep 2s

Type "clear"
Enter
Sleep 500ms

# @step Explore a Specific Skill
# @docs-brief Examine the structure of a skill definition
# @book-detail Skills follow a structured format with YAML frontmatter defining metadata (name, description, tools, complexity) and markdown content defining the workflow. Let's look at a validation skill.

Type "# Look at the plugin-validator skill structure"
Enter
Sleep 500ms

Type "head -30 plugins/abstract/skills/plugin-validator/SKILL.md"
Enter
Sleep 3s

Type "clear"
Enter
Sleep 500ms

# @step Validate a Plugin
# @docs-brief Use abstract:plugin-validator to check plugin structure
# @book-detail The abstract plugin provides meta-skills for plugin development. The plugin-validator skill checks that plugins follow the correct structure, have valid metadata, and properly define their skills and commands.

Type "# In Claude Code, you would invoke this skill with:"
Enter
Sleep 500ms

Type "# Skill(abstract:plugin-validator, plugin_name='sanctum')"
Enter
Sleep 1s

Type "echo ''"
Enter
Sleep 500ms

Type "# This would validate:"
Enter
Sleep 500ms

Type "# - Plugin structure and directories"
Enter
Sleep 500ms

Type "# - SKILL.md frontmatter and formatting"
Enter
Sleep 500ms

Type "# - Command definitions"
Enter
Sleep 500ms

Type "# - Dependencies between skills"
Enter
Sleep 2s

Type "clear"
Enter
Sleep 500ms

# @step Show Real Skill Usage in Workflow
# @docs-brief Demonstrate git-workspace-review skill
# @book-detail The sanctum:git-workspace-review skill is commonly used at the start of development sessions to understand the current state of a git repository. It analyzes branch status, recent commits, and changed files.

Type "# Example: git-workspace-review skill in action"
Enter
Sleep 500ms

Type "# This skill would:"
Enter
Sleep 500ms

Type "echo '1. Run git status to see uncommitted changes'"
Enter
Sleep 500ms

Type "echo '2. Run git log to see recent commit history'"
Enter
Sleep 500ms

Type "echo '3. Analyze changed files and their impact'"
Enter
Sleep 500ms

Type "echo '4. Provide context for the current development session'"
Enter
Sleep 2s

Type "clear"
Enter
Sleep 500ms

# @step Skills Enable Workflow Automation
# @docs-brief Show how skills compose into complex workflows
# @book-detail Skills are designed to be composable. Complex workflows like code review or PR preparation chain multiple skills together, each contributing its specialized knowledge.

Type "# Skills compose into powerful workflows:"
Enter
Sleep 500ms

Type "echo ''"
Enter
Sleep 500ms

Type "echo 'PR Preparation Workflow:'"
Enter
Sleep 500ms

Type "echo '  1. Skill(sanctum:git-workspace-review) - Understand changes'"
Enter
Sleep 500ms

Type "echo '  2. Skill(imbue:scope-guard) - Check scope drift'"
Enter
Sleep 500ms

Type "echo '  3. Skill(sanctum:commit-messages) - Generate commit msg'"
Enter
Sleep 500ms

Type "echo '  4. Skill(sanctum:pr-prep) - Prepare PR description'"
Enter
Sleep 2s

Type "clear"
Enter
Sleep 500ms

# @step Development Value Proposition
# @docs-brief Recap the value of skills for development workflows
# @book-detail Skills transform Claude Code from a general assistant into a specialized development partner. They encode best practices, automate repetitive tasks, and ensure consistency across workflows.

Type "echo '✓ 105 skills across 14 plugins'"
Enter
Sleep 500ms

Type "echo '✓ Structured workflows for git, review, specs, testing'"
Enter
Sleep 500ms

Type "echo '✓ Composable and reusable across projects'"
Enter
Sleep 500ms

Type "echo '✓ Self-documenting with clear dependencies'"
Enter
Sleep 500ms

Type "echo '✓ Validated structure ensures quality'"
Enter
Sleep 2s

Sleep 3s
