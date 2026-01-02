# VHS Tape Syntax Reference

## Metadata Comments

Custom metadata annotations for documentation integration:

```tape
# @title: Command Demo
# @description: Demonstrates the CLI workflow
# @step: 1
# @docs-brief: Quick overview for documentation
# @book-detail: Extended explanation for book chapters
```

## Output Directive

Specifies the output file path (required):

```tape
Output demo.gif
```

Supported formats: `.gif`, `.mp4`, `.webm`

## Set Directives

Configure terminal appearance and behavior:

```tape
# Typography
Set FontSize 14
Set FontFamily "JetBrains Mono"

# Dimensions
Set Width 1200
Set Height 600

# Appearance
Set Theme "Dracula"
Set Padding 20
Set Margin 10
Set MarginFill "#674EFF"
Set BorderRadius 8

# Timing
Set TypingSpeed 50ms
Set Framerate 60

# Environment
Set Env "TERM" "xterm-256color"
Set Env "PS1" "$ "

# Window
Set Shell "bash"
Set WindowBar Colorful
Set WindowBarSize 40
```

## Action Commands

### Type

Types text into the terminal:

```tape
Type "echo 'Hello World'"
Type@50ms "slower typing"
```

### Enter

Sends Enter key (execute command):

```tape
Enter
```

### Sleep

Pause for duration:

```tape
Sleep 500ms
Sleep 2s
```

### Key Combinations

```tape
Ctrl+C
Ctrl+D
Ctrl+L
Escape
Tab
Backspace
Up
Down
Left
Right
Space
```

### Screenshot

Capture a still frame:

```tape
Screenshot output.png
```

### Hide/Show

Control visibility of actions:

```tape
Hide
Type "secret setup commands"
Enter
Show
```

## Advanced Features

### Split Panes

Create multi-pane layouts:

```tape
Split
Type@left "echo 'Left pane'"
Enter@left
Type@right "echo 'Right pane'"
Enter@right
```

### Source

Include other tape files:

```tape
Source common-setup.tape
```

### Require

validate programs are available:

```tape
Require echo
Require git
```

## Complete Example

```tape
# @title: Git Status Demo
# @description: Shows git status workflow
# @step: 1

Output git-demo.gif

Set FontSize 16
Set Width 1000
Set Height 400
Set Theme "Catppuccin Mocha"
Set TypingSpeed 75ms

Hide
Type "cd ~/project"
Enter
Sleep 500ms
Show

Type "git status"
Sleep 500ms
Enter
Sleep 2s

Type "git add ."
Sleep 500ms
Enter
Sleep 1s

Type "git commit -m 'Update docs'"
Sleep 500ms
Enter
Sleep 2s
```
