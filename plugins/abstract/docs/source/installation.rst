Installation
============

Requirements
------------

- Python 3.12 or higher
- Claude Code with marketplace support

Installing the Plugin
---------------------

1. **Add to Marketplace**

   Add the following to your ``~/.claude/marketplace.json``:

   .. code-block:: json

      {
        "name": "abstract",
        "source": {
          "source": "url",
          "url": "https://github.com/athola/abstract.git"
        },
        "description": "Meta-skills infrastructure for Claude Code plugin ecosystem",
        "version": "1.0.0",
        "strict": true
      }

2. **Restart Claude Code**

   Restart Claude Code for the plugin to be detected and loaded.

Development Setup
-----------------

For development or testing:

1. **Clone Repository**

   .. code-block:: bash

      git clone https://github.com/athola/abstract.git
      cd abstract

2. **Install Dependencies**

   .. code-block:: bash

      # Using uv (recommended)
      uv sync --dev

      # Or using pip
      python -m pip install -e ".[dev]"

3. **Verify Installation**

   .. code-block:: bash

      make test

4. **Install Pre-commit Hooks**

   .. code-block:: bash

      make install-hooks

Directory Structure
------------------

After installation, the plugin provides:

.. code-block:: text

   abstract/
   ├── skills/                    # Skill implementations
   │   ├── modular-skills/        # Modular design patterns
   │   └── skills-eval/           # Evaluation tools
   ├── scripts/                   # Utility scripts
   │   ├── token_estimator.py     # Token usage analysis
   │   ├── context_optimizer.py   # Context optimization
   │   ├── skill_analyzer.py      # Skill complexity analysis
   │   └── abstract_validator.py # Validation tools
   └── src/abstract/              # Python package
       ├── cli_framework.py       # CLI base classes
       ├── config.py              # Configuration management
       ├── frontmatter.py         # Frontmatter processing
       ├── utils.py               # Utility functions
       └── skills_eval.py         # Evaluation logic

Configuration
-------------

The plugin uses configuration files in YAML format:

.. code-block:: yaml

   # .abstract/config.yaml
   skills_dir: "skills"
   token_limit: 4000
   optimization:
     context_window: 128000
     aggressive: false

Configuration locations (in order of precedence):

1. ``--config`` command-line argument
2. ``.abstract/config.yaml`` in project root
3. ``~/.config/abstract/config.yaml``
4. Default settings

Troubleshooting
---------------

Plugin Not Detected
~~~~~~~~~~~~~~~~~~~

1. Check that ``marketplace.json`` is valid JSON
2. Verify the URL is accessible
3. Restart Claude Code completely
4. Check the Claude Code logs for errors

Scripts Not Working
~~~~~~~~~~~~~~~~~~~

1. Ensure dependencies are installed:

   .. code-block:: bash

      uv sync --dev

2. Check Python path in scripts:

   .. code-block:: bash

      python3 scripts/token_estimator.py --help

3. Verify src/abstract is importable:

   .. code-block:: python

      import sys
      from pathlib import Path
      sys.path.insert(0, str(Path.cwd() / "src"))
      from abstract import utils

Permission Errors
~~~~~~~~~~~~~~~~

1. Make scripts executable:

   .. code-block:: bash

      chmod +x scripts/*.py

2. Or use Python directly:

   .. code-block:: bash

      python3 scripts/script.py

Import Errors
~~~~~~~~~~~~~

If you see import errors, ensure:

1. You're in the project root directory
2. The ``src`` directory exists
3. Python 3.12+ is being used

.. code-block:: bash

   python3 --version  # Should be 3.12+
   ls src/abstract    # Should list Python files