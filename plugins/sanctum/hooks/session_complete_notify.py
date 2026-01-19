#!/usr/bin/env python3
"""Cross-platform toast notification when Claude session awaits input.

Supports: Linux (notify-send), macOS (osascript), Windows (PowerShell toast).
"""

import html
import os
import platform
import re
import subprocess
import sys


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
            timeout=1,  # Reduced from 3s
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as e:
        print(f"[sanctum:notify] Linux notification failed: {e}", file=sys.stderr)
        return False


def notify_macos(title: str, message: str) -> bool:
    """Send notification on macOS using osascript."""
    # Escape for AppleScript string literals
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_message = message.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'display notification "{safe_message}" '
        f'with title "{safe_title}" sound name "Glass"'
    )
    try:
        subprocess.run(  # noqa: S603
            ["osascript", "-e", script],  # noqa: S607
            check=True,
            timeout=1,  # Reduced from 3s
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as e:
        print(f"[sanctum:notify] macOS notification failed: {e}", file=sys.stderr)
        return False


def notify_windows(title: str, message: str) -> bool:
    """Send notification on Windows using PowerShell toast."""
    # Escape for XML content (prevents injection via <, >, &, ", ')
    safe_title = html.escape(title)
    safe_message = html.escape(message)

    # PowerShell script for Windows toast notification
    # Note: Long lines below are PowerShell code that requires specific formatting
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
    <audio src="ms-winsoundevent:Notification.Default"/>
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
            timeout=2,  # Reduced from 5s
            capture_output=True,
        )
        return True
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as e:
        print(f"[sanctum:notify] Windows toast failed: {e}", file=sys.stderr)
        # Fallback: try simpler BurntToast if available
        # Escape for PowerShell string (backtick escapes quotes)
        ps_title = title.replace('"', '`"')
        ps_message = message.replace('"', '`"')
        try:
            burnt_cmd = f'New-BurntToastNotification -Text "{ps_title}", "{ps_message}"'
            subprocess.run(  # noqa: S603
                ["powershell", "-NoProfile", "-Command", burnt_cmd],  # noqa: S607
                check=True,
                timeout=2,  # Reduced from 5s
                capture_output=True,
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            print(f"[sanctum:notify] BurntToast fallback failed: {e}", file=sys.stderr)
            return False


def is_wsl() -> bool:
    """Detect if running in Windows Subsystem for Linux."""
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def notify_wsl(title: str, message: str) -> bool:
    """Send notification on WSL using Windows PowerShell.

    WSL can call Windows executables directly via the /mnt/c path or just
    'powershell.exe' if interop is enabled.
    """
    # Escape for XML content (prevents injection via <, >, &, ", ')
    safe_title = html.escape(title)
    safe_message = html.escape(message)

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
    <audio src="ms-winsoundevent:Notification.Default"/>
</toast>
"@

$xml = New-Object {xml_doc}
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[{toast_mgr}]::CreateToastNotifier("Claude Code").Show($toast)
"""
    # Try multiple PowerShell paths for WSL compatibility
    powershell_paths = [
        "powershell.exe",  # WSL interop (if enabled)
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
            continue  # Try next path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            msg = f"[sanctum:notify] WSL PowerShell failed ({ps_path}): {e}"
            print(msg, file=sys.stderr)
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

    print(
        "[sanctum:notify] WSL notification failed: no working PowerShell path",
        file=sys.stderr,
    )
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


def main() -> None:
    """Send notification that Claude session is awaiting input."""
    # Skip if notifications disabled via environment variable
    if os.environ.get("CLAUDE_NO_NOTIFICATIONS") == "1":
        sys.exit(0)

    # Run notification in subprocess - don't block the hook
    # Use Popen (not run) to avoid waiting for completion
    script_path = __file__
    try:
        subprocess.Popen(  # noqa: S603
            [sys.executable, script_path, "--background"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent
        )
    except Exception:  # noqa: S110 (intentional silent fail for non-critical notifications)
        # Fail silently - notifications are non-critical
        pass

    # Exit immediately - notification runs in background
    sys.exit(0)


def run_notification() -> None:
    """Actually send the notification (called in background)."""
    try:
        terminal_info = get_terminal_info()
        title = "Claude Code Ready"
        message = f"Awaiting input in: {terminal_info}"
        send_notification(title, message)
    except Exception:  # noqa: S110 (intentional silent fail for non-critical notifications)
        # Silently fail - notifications are non-critical
        pass


if __name__ == "__main__":
    # Check if running in background mode
    if len(sys.argv) > 1 and sys.argv[1] == "--background":
        run_notification()
    else:
        main()
