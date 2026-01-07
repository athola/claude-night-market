# Skills Showcase - REAL Interactive Claude CLI
# Demonstrates actual skill discovery with the claude command

# IMPORTANT: Must run from assets/tapes/ directory for relative paths
Output ../gifs/skills-showcase.gif

# CRITICAL: Memory-optimized settings to prevent terminal crashes
Set FontSize 14
Set Width 1000
Set Height 700
Set Theme "Catppuccin Mocha"
Set TypingSpeed 100ms
Set PlaybackSpeed 1.0
Set Shell "bash"
Set Padding 20

# Start in project directory
Type "cd /home/alext/claude-night-market" Enter
Sleep 500ms
Type "clear" Enter
Sleep 500ms

# Show banner
Type "echo 'Skills: Claude CLI Demonstration'" Enter
Sleep 1s

# Start REAL Claude CLI in interactive mode
Type "echo 'Starting interactive Claude session...'" Enter
Sleep 1s

# Launch Claude
Type "claude" Enter
Sleep 10s

# Demonstrate skill discovery with Claude
# Type a prompt that will trigger skill auto-discovery
Type "Show me the fix-issue skill documentation" Enter
Sleep 15s

# Ask about another skill
Type "What skills are available in the sanctum plugin?" Enter
Sleep 15s

# Demonstrate context-aware skill loading
Type "I need to prepare a pull request" Enter
Sleep 15s

# Exit Claude
Type "exit" Enter
Sleep 5s

# Final summary
Type "echo '✓ Real Claude CLI with skill auto-discovery'" Enter
Sleep 5s
