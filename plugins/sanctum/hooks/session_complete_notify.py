#!/usr/bin/env python3
"""
Cross-platform toast notification when Claude session awaits input.
Supports: Linux (notify-send), macOS (osascript), Windows (PowerShell toast).
"""

import html
import os
import platform
import subprocess
import sys


def get_terminal_info() -> str:
    """Get terminal/session identifier for the notification."""
    # Try common terminal identification methods
    term_program = os.environ.get("TERM_PROGRAM", "")

    # Get working directory as context
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)

    # Try to get terminal title or session info
    if term_program:
        return f"{term_program} - {project_name}"

    # Check for tmux/screen session
    tmux = os.environ.get("TMUX", "")
    if tmux:
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#S:#W"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"tmux:{result.stdout.strip()} - {project_name}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check for SSH session
    ssh_tty = os.environ.get("SSH_TTY", "")
    if ssh_tty:
        return f"SSH - {project_name}"

    # Fallback: use TTY name or generic
    tty = os.environ.get("TTY", os.environ.get("GPG_TTY", ""))
    if tty:
        return f"{os.path.basename(tty)} - {project_name}"

    return project_name


def notify_linux(title: str, message: str) -> bool:
    """Send notification on Linux using notify-send."""
    try:
        subprocess.run(
            [
                "notify-send",
                "--app-name=Claude Code",
                "--urgency=normal",
                title,
                message,
            ],
            check=True,
            timeout=3,
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
    script = f'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=3)
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

    # PowerShell script for Windows toast notification
    ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{safe_title}</text>
            <text id="2">{safe_message}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Default"/>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code").Show($toast)
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            check=True,
            timeout=5,
            capture_output=True,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        # Fallback: try simpler BurntToast if available
        # Escape for PowerShell string (backtick escapes quotes)
        ps_title = title.replace('"', '`"')
        ps_message = message.replace('"', '`"')
        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f'New-BurntToastNotification -Text "{ps_title}", "{ps_message}"',
                ],
                check=True,
                timeout=5,
                capture_output=True,
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False


def send_notification(title: str, message: str) -> bool:
    """Send notification based on current platform."""
    system = platform.system().lower()

    if system == "linux" or "wsl" in platform.release().lower():
        return notify_linux(title, message)
    elif system == "darwin":
        return notify_macos(title, message)
    elif system == "windows":
        return notify_windows(title, message)
    else:
        return False


def main():
    terminal_info = get_terminal_info()
    title = "Claude Code Ready"
    message = f"Awaiting input in: {terminal_info}"

    send_notification(title, message)

    # Exit silently regardless - don't interrupt Claude's flow
    sys.exit(0)


if __name__ == "__main__":
    main()
