# Skills Showcase - REAL Interactive Claude CLI
# Demonstrates actual skill discovery with the claude command

# USAGE: Run from project root with:
#   vhs assets/tapes/skills-showcase.tape
#
# Output will be: assets/gifs/skills-showcase.gif
# Note: VHS displays "../gifs/..." in output but creates the file correctly
# Wait ~10s after "Creating..." message before opening (large file write)
Output assets/gifs/skills-showcase.gif

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

# Launch Claude (skip permission prompts for cleaner demo)
Type "claude --dangerously-skip-permissions" Enter
Sleep 10s

# Ask about a skill
Type "What skills are available in the parseltongue plugin? Provide a summary in 20 lines or less." Enter
Sleep 35s

# Ask about a skill
Type "Provide some examples in 20 lines or less of how I can incorporate parseltongue plugin into my workflow." Enter
Sleep 35s

# Exit Claude
Type "exit" Enter
Sleep 5s

# Final summary
Type "echo '✓ Real Claude CLI with skill auto-discovery'" Enter
Sleep 5s
