---
name: uninstall-watchdog
description: >-
  Remove the egregore watchdog daemon and clean up files
usage: /egregore:uninstall-watchdog
---

# uninstall-watchdog

Remove the egregore watchdog daemon and clean up all
related files.

## What It Does

On macOS, unloads and removes the launchd agent plist at
`~/Library/LaunchAgents/com.egregore.watchdog.plist`.

On Linux, disables and removes the systemd user timer
and service files for `egregore-watchdog`.

## Files Removed

- macOS: `~/Library/LaunchAgents/com.egregore.watchdog.plist`
- Linux: `~/.config/systemd/user/egregore-watchdog.timer`
- Linux: `~/.config/systemd/user/egregore-watchdog.service`

The `.egregore/` directory and its contents (manifest,
budget, logs) are not removed. Delete them manually if
you no longer need them.

## See Also

- `/egregore:install-watchdog` to reinstall.
- `/egregore:dismiss` to stop the egregore without
  removing the daemon.
