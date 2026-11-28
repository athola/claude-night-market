---
name: uninstall-watchdog
description: >-
  Remove the egregore watchdog daemon and clean up files
usage: /egregore:uninstall-watchdog
---

# uninstall-watchdog

Remove the egregore watchdog daemon and clean up all
related files.

Invoke `Skill(egregore:uninstall-watchdog-playbook)`, which carries the
uninstall steps and the list of files removed.

## See Also

- `/egregore:install-watchdog` to reinstall.
- `/egregore:dismiss` to stop the egregore without
  removing the daemon.
