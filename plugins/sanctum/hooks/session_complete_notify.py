#!/usr/bin/env python3
"""Cross-platform toast notification when Claude session awaits input.

Supports: Linux (notify-send), macOS (osascript), Windows (PowerShell toast).

Deduplication strategy (prevents multiple notifications from same event):
1. Per-session tracking: Only one notification per session until user input
2. Content deduplication: Skip duplicate title+message within time window
3. Time-based debouncing: Skip if notification sent within N seconds
"""

import hashlib
import html
import json
import os
import platform
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Configuration (can be overridden via environment variables)
DEBOUNCE_SECONDS = int(os.environ.get("CLAUDE_NOTIFY_DEBOUNCE", "5"))
CONTENT_DEDUP_SECONDS = int(os.environ.get("CLAUDE_NOTIFY_CONTENT_DEDUP", "30"))


@dataclass
class NotificationState:
    """Tracks notification state per terminal session."""

    last_notify_time: float = 0.0
    last_content_hash: str = ""
    notified_since_input: bool = False
    session_id: str = ""

    @classmethod
    def state_file_path(cls, session_id: str) -> Path:
        """Get path to state file for given session."""
        # Sanitize session_id for filesystem
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)[:64]
        return Path(f"/tmp/.claude-notify-{safe_id}.json")  # noqa: S108

    @classmethod
    def load(cls, session_id: str) -> "NotificationState":
        """Load state from file, or return fresh state if not found."""
        state_file = cls.state_file_path(session_id)
        try:
            if state_file.exists():
                data = json.loads(state_file.read_text())
                return cls(
                    last_notify_time=data.get("last_notify_time", 0.0),
                    last_content_hash=data.get("last_content_hash", ""),
                    notified_since_input=data.get("notified_since_input", False),
                    session_id=session_id,
                )
        except (OSError, json.JSONDecodeError):
            pass
        return cls(session_id=session_id)

    def save(self) -> None:
        """Persist state to file."""
        state_file = self.state_file_path(self.session_id)
        try:
            state_file.write_text(json.dumps(asdict(self)))
        except OSError:
            pass  # Non-critical, fail silently

    def clear_input_flag(self) -> None:
        """Clear the notified_since_input flag (called on user input)."""
        self.notified_since_input = False
        self.save()

    def should_notify(self, content_hash: str) -> tuple[bool, str]:
        """Check if notification should be sent. Returns (should_send, reason)."""
        now = time.time()
        time_since_last = now - self.last_notify_time

        # Layer 1: Per-session tracking - skip if already notified since last input
        if self.notified_since_input:
            return False, "already_notified_since_input"

        # Layer 2: Content deduplication - skip if same content within window
        if (
            content_hash == self.last_content_hash
            and time_since_last < CONTENT_DEDUP_SECONDS
        ):
            return False, f"duplicate_content_within_{CONTENT_DEDUP_SECONDS}s"

        # Layer 3: Time-based debouncing - skip if too recent
        if time_since_last < DEBOUNCE_SECONDS:
            return False, f"debounced_within_{DEBOUNCE_SECONDS}s"

        return True, "ok"

    def record_notification(self, content_hash: str) -> None:
        """Record that a notification was sent."""
        self.last_notify_time = time.time()
        self.last_content_hash = content_hash
        self.notified_since_input = True
        self.save()


def get_session_id() -> str:
    """Generate a unique session identifier for the current terminal."""
    parts: list[str] = []

    # Include project directory
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)
    parts.append(project_name)

    # Priority 1: Zellij session + tab
    zellij_session = os.environ.get("ZELLIJ_SESSION_NAME", "")
    if zellij_session:
        parts.insert(0, f"zellij_{zellij_session}")
        tab_name = get_zellij_tab_name()
        if tab_name:
            parts.insert(1, tab_name)
        return "_".join(parts)

    # Priority 2: tmux session:window
    if os.environ.get("TMUX", ""):
        tmux_info = _get_tmux_session()
        if tmux_info:
            parts.insert(0, f"tmux_{tmux_info.replace(':', '_')}")
            return "_".join(parts)

    # Priority 3: SSH + TTY
    if tty := os.environ.get("SSH_TTY", os.environ.get("TTY", "")):
        parts.insert(0, f"tty_{os.path.basename(tty)}")
        return "_".join(parts)

    # Priority 4: Terminal program + PID
    if term_program := os.environ.get("TERM_PROGRAM", ""):
        ppid = os.environ.get("PPID", str(os.getppid()))
        parts.insert(0, f"{term_program}_{ppid}")
        return "_".join(parts)

    # Fallback: just use project name with parent PID
    ppid = os.environ.get("PPID", str(os.getppid()))
    parts.insert(0, f"term_{ppid}")
    return "_".join(parts)


def content_hash(title: str, message: str) -> str:
    """Generate a hash of notification content for deduplication."""
    content = f"{title}|{message}"
    return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:16]


def get_zellij_tab_name() -> str | None:
    """Get current Zellij tab name from layout dump."""
    try:
        result = subprocess.run(
            ["zellij", "action", "dump-layout"],  # noqa: S603,S607
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        if result.returncode == 0:
            # Parse layout to find focused tab: tab name="TabName" focus=true
            match = re.search(r'tab name="([^"]+)"[^}]*focus=true', result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _get_tmux_session() -> str | None:
    """Get tmux session:window name."""
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#S:#W"],  # noqa: S603,S607
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_terminal_info() -> str:
    """Get terminal/session identifier for the notification."""
    # Get working directory as context
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)
    session_prefix = ""

    # Priority 1: Check for Zellij session (popular terminal multiplexer)
    zellij_session = os.environ.get("ZELLIJ_SESSION_NAME", "")
    if zellij_session:
        tab_name = get_zellij_tab_name()
        if tab_name and tab_name != "Tab #1":  # Skip default tab name
            session_prefix = f"zellij:{zellij_session}|{tab_name}"
        else:
            session_prefix = f"zellij:{zellij_session}"

    # Priority 2: Check for tmux/screen session
    elif os.environ.get("TMUX", ""):
        tmux_info = _get_tmux_session()
        if tmux_info:
            session_prefix = f"tmux:{tmux_info}"

    # Priority 3: Use TERM_PROGRAM (e.g., iTerm, Terminal.app)
    elif term_program := os.environ.get("TERM_PROGRAM", ""):
        session_prefix = term_program

    # Priority 4: SSH session indicator
    elif os.environ.get("SSH_TTY", ""):
        session_prefix = "SSH"

    # Priority 5: TTY name
    elif tty := os.environ.get("TTY", os.environ.get("GPG_TTY", "")):
        session_prefix = os.path.basename(tty)

    # Format final output
    if session_prefix:
        return f"{session_prefix} - {project_name}"
    return project_name


def notify_linux(title: str, message: str) -> bool:
    """Send notification on Linux using notify-send."""
    try:
        subprocess.run(  # noqa: S603
            [
                "/usr/bin/notify-send",
                "--app-name=Claude Code",
                "--urgency=normal",
                title,
                message,
            ],
            check=True,
            timeout=1,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return False


def notify_macos(title: str, message: str) -> bool:
    """Send notification on macOS using osascript."""
    # Escape for AppleScript string literals
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_message = message.replace("\\", "\\\\").replace('"', '\\"')

    # Check if sound is disabled via environment variable
    sound_enabled = os.environ.get("CLAUDE_NOTIFICATION_SOUND", "1") != "0"
    sound_suffix = ' sound name "Glass"' if sound_enabled else ""

    script = (
        f'display notification "{safe_message}" with title "{safe_title}"{sound_suffix}'
    )
    try:
        subprocess.run(  # noqa: S603
            ["osascript", "-e", script],  # noqa: S607
            check=True,
            timeout=1,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return False


def notify_windows(title: str, message: str) -> bool:
    """Send notification on Windows using PowerShell toast."""
    # Escape for XML content (prevents injection via <, >, &, ", ')
    safe_title = html.escape(title)
    safe_message = html.escape(message)

    # Check if sound is disabled via environment variable
    sound_enabled = os.environ.get("CLAUDE_NOTIFICATION_SOUND", "1") != "0"
    audio_element = (
        '<audio src="ms-winsoundevent:Notification.Default"/>'
        if sound_enabled
        else '<audio silent="true"/>'
    )

    # PowerShell script for Windows toast notification
    toast_mgr = "Windows.UI.Notifications.ToastNotificationManager"
    xml_doc = "Windows.Data.Xml.Dom.XmlDocument"
    ps_script = f"""
[{toast_mgr}, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[{xml_doc}, {xml_doc}, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{safe_title}</text>
            <text id="2">{safe_message}</text>
        </binding>
    </visual>
    {audio_element}
</toast>
"@

$xml = New-Object {xml_doc}
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[{toast_mgr}]::CreateToastNotifier("Claude Code").Show($toast)
"""
    try:
        subprocess.run(  # noqa: S603
            ["powershell", "-NoProfile", "-Command", ps_script],  # noqa: S607
            check=True,
            timeout=2,
            capture_output=True,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        # Fallback: try simpler BurntToast if available
        ps_title = title.replace('"', '`"')
        ps_message = message.replace('"', '`"')
        try:
            burnt_cmd = f'New-BurntToastNotification -Text "{ps_title}", "{ps_message}"'
            subprocess.run(  # noqa: S603
                ["powershell", "-NoProfile", "-Command", burnt_cmd],  # noqa: S607
                check=True,
                timeout=2,
                capture_output=True,
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False


def is_wsl() -> bool:
    """Detect if running in Windows Subsystem for Linux."""
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def notify_wsl(title: str, message: str) -> bool:
    """Send notification on WSL using Windows PowerShell."""
    # Escape for XML content (prevents injection via <, >, &, ", ')
    safe_title = html.escape(title)
    safe_message = html.escape(message)

    # Check if sound is disabled via environment variable
    sound_enabled = os.environ.get("CLAUDE_NOTIFICATION_SOUND", "1") != "0"
    audio_element = (
        '<audio src="ms-winsoundevent:Notification.Default"/>'
        if sound_enabled
        else '<audio silent="true"/>'
    )

    # PowerShell script for Windows toast notification
    toast_mgr = "Windows.UI.Notifications.ToastNotificationManager"
    xml_doc = "Windows.Data.Xml.Dom.XmlDocument"
    ps_script = f"""
[{toast_mgr}, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[{xml_doc}, {xml_doc}, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{safe_title}</text>
            <text id="2">{safe_message}</text>
        </binding>
    </visual>
    {audio_element}
</toast>
"@

$xml = New-Object {xml_doc}
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[{toast_mgr}]::CreateToastNotifier("Claude Code").Show($toast)
"""
    # Try multiple PowerShell paths for WSL compatibility
    powershell_paths = [
        "powershell.exe",
        "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe",
    ]

    for ps_path in powershell_paths:
        try:
            subprocess.run(  # noqa: S603
                [ps_path, "-NoProfile", "-Command", ps_script],
                check=True,
                timeout=3,
                capture_output=True,
            )
            return True
        except FileNotFoundError:
            continue
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue

    # Fallback: try BurntToast if available
    ps_title = title.replace('"', '`"')
    ps_message = message.replace('"', '`"')
    for ps_path in powershell_paths:
        try:
            burnt_cmd = f'New-BurntToastNotification -Text "{ps_title}", "{ps_message}"'
            subprocess.run(  # noqa: S603
                [ps_path, "-NoProfile", "-Command", burnt_cmd],
                check=True,
                timeout=3,
                capture_output=True,
            )
            return True
        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ):
            continue

    return False


def send_notification(title: str, message: str) -> bool:
    """Send notification based on current platform."""
    system = platform.system().lower()

    # Check WSL first - it reports as Linux but should use Windows notifications
    if system == "linux" and is_wsl():
        return notify_wsl(title, message)
    elif system == "linux":
        return notify_linux(title, message)
    elif system == "darwin":
        return notify_macos(title, message)
    elif system == "windows":
        return notify_windows(title, message)
    else:
        return False


def clear_notification_state() -> None:
    """Clear the 'notified since input' flag for current session.

    Called by UserPromptSubmit hook to signal user has interacted,
    allowing the next Stop event to trigger a notification.
    """
    try:
        session_id = get_session_id()
        state = NotificationState.load(session_id)
        state.clear_input_flag()
    except Exception:  # noqa: S110, BLE001
        pass  # Non-critical, fail silently


def main() -> None:
    """Send notification that Claude session is awaiting input."""
    # Skip if notifications disabled via environment variable
    if os.environ.get("CLAUDE_NO_NOTIFICATIONS") == "1":
        sys.exit(0)

    # Run notification in subprocess - don't block the hook
    # Use Popen (not run) to avoid waiting for completion
    # Pass session_id and cwd to background process (env vars may not persist)
    script_path = __file__
    session_id = get_session_id()
    cwd = os.getcwd()
    try:
        subprocess.Popen(  # noqa: S603
            [sys.executable, script_path, "--background", session_id, cwd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent
        )
    except Exception:  # noqa: S110 (intentional silent fail for non-critical notifications)
        # Fail silently - notifications are non-critical
        pass

    # Exit immediately - notification runs in background
    sys.exit(0)


def run_notification(session_id: str, cwd: str) -> None:
    """Actually send the notification (called in background).

    Args:
        session_id: Pre-computed session identifier from parent process.
        cwd: Working directory from parent process.
    """
    try:
        # Change to original working directory for terminal info
        os.chdir(cwd)

        terminal_info = get_terminal_info()
        title = "Claude Code Ready"
        message = f"Awaiting input in: {terminal_info}"

        # Load state and check if we should notify
        state = NotificationState.load(session_id)
        msg_hash = content_hash(title, message)

        should_send, _reason = state.should_notify(msg_hash)

        if not should_send:
            # Deduplication filtered this notification
            return

        # Send the notification
        if send_notification(title, message):
            # Record successful notification
            state.record_notification(msg_hash)

    except Exception:  # noqa: S110, BLE001 (intentional silent fail for non-critical)
        # Silently fail - notifications are non-critical
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clear-state":
            # Called by UserPromptSubmit hook to reset notification state
            clear_notification_state()
        elif sys.argv[1] == "--background" and len(sys.argv) >= 4:
            # Background mode with session_id and cwd
            run_notification(session_id=sys.argv[2], cwd=sys.argv[3])
        elif sys.argv[1] == "--background":
            # Legacy background mode (fallback)
            run_notification(session_id=get_session_id(), cwd=os.getcwd())
    else:
        main()
