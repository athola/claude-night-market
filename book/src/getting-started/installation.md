# Installation

This guide walks you through adding the Claude Night Market to your Claude Code setup.

## Step 1: Add the Marketplace

Open Claude Code and run:

```bash
/plugin marketplace add athola/claude-night-market
```

This registers the marketplace, making all plugins available for installation.

<div class="achievement-unlock" data-achievement="marketplace-added">
Achievement Unlocked: Marketplace Pioneer
</div>

## Step 2: Browse Available Plugins

View the marketplace contents:

```bash
/plugin marketplace list
```

You'll see plugins organized by layer:

| Layer | Plugins | Purpose |
|-------|---------|---------|
| Meta | abstract | Plugin infrastructure |
| Foundation | imbue, sanctum, leyline | Core workflows |
| Utility | conservation, conjure | Resource optimization |
| Domain | archetypes, pensive, parseltongue, memory-palace, spec-kit, minister | Specialized tasks |

## Step 3: Install Individual Plugins

Install plugins based on your needs:

```bash
# Git and workspace operations
/plugin install sanctum@claude-night-market

# Specification-driven development
/plugin install spec-kit@claude-night-market

# Code review toolkit
/plugin install pensive@claude-night-market

# Python development
/plugin install parseltongue@claude-night-market
```

## Step 4: Verify Installation

Check that plugins loaded correctly:

```bash
/plugin list
```

Installed plugins appear with their available skills and commands.

## Optional: Install Superpowers

For enhanced methodology integration:

```bash
# Add superpowers marketplace
/plugin marketplace add obra/superpowers

# Install superpowers
/plugin install superpowers@superpowers-marketplace
```

Superpowers provides TDD cycles, systematic debugging, and code review patterns that enhance Night Market plugins.

## Recommended Plugin Sets

### Minimal Setup
For basic git workflows:
```bash
/plugin install sanctum@claude-night-market
```

### Development Setup
For active feature development:
```bash
/plugin install sanctum@claude-night-market
/plugin install imbue@claude-night-market
/plugin install spec-kit@claude-night-market
```

### Full Setup
For detailed workflow coverage:
```bash
/plugin install abstract@claude-night-market
/plugin install imbue@claude-night-market
/plugin install sanctum@claude-night-market
/plugin install leyline@claude-night-market
/plugin install conservation@claude-night-market
/plugin install pensive@claude-night-market
/plugin install spec-kit@claude-night-market
```

## Troubleshooting

### Plugin not loading?

1. Verify marketplace was added: `/plugin marketplace list`
2. Check for typos in plugin name
3. Restart Claude Code session

### Conflicts between plugins?

Plugins are designed to be composable. If you experience issues:
1. Check the plugin's README for dependency requirements
2. validate foundation plugins (imbue, leyline) are installed if using domain plugins

## Next Steps

Continue to [Your First Plugin](first-plugin.md) for a hands-on tutorial.
