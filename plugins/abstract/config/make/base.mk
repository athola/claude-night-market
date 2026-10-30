# config/make/base.mk - Shell settings and the unknown-target guard
# Included by common.mk and markdown-only.mk, so both kinds of plugin
# run recipes under the same shell and refuse the same unknown targets.

SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# .SHELLFLAGS arrived in GNU make 3.82. Stock macOS ships 3.81 from the
# Xcode command line tools, which parses the assignment above and ignores
# it. 3.81 does honor flags written into SHELL itself, so for the releases
# that ignore .SHELLFLAGS the flags go there, and every make runs recipes
# under -euo pipefail. The filter names the releases that ignore the
# assignment, so a make newer than 4.x keeps the plain form.
ifneq ($(filter 3.7% 3.80 3.81,$(firstword $(MAKE_VERSION))),)
SHELL := /bin/bash -euo pipefail
endif

# No .ONESHELL. 3.81 ignores it, so every recipe here was written to run
# one line per shell, and on 3.82+ it changed that: a mid-recipe exit
# ended the recipe and a cd leaked into later lines. One semantics on
# every make.

# Guard against accidental file creation (catch-all for unknown targets).
# A plugin that includes Makefile.local declares `Makefile.local:;` so this
# rule does not claim it.
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
