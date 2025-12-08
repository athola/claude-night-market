Quick Start Guide
==================

Getting Started with Abstract
----------------------------

Installation
~~~~~~~~~~~~

1. Add Abstract to your ``marketplace.json``:

.. code-block:: json

   {
     "name": "abstract",
     "source": {
       "source": "url",
       "url": "https://github.com/athola/abstract.git"
     },
     "description": "Meta-skills infrastructure for Claude Code",
     "version": "1.0.0",
     "strict": true
   }

2. Install dependencies:

.. code-block:: bash

   make check
   # OR
   uv sync --dev

3. Run the verification:

.. code-block:: bash

   make test

Basic Usage
~~~~~~~~~~~

Token Usage Analysis
^^^^^^^^^^^^^^^^^^

Analyze a single skill file:

.. code-block:: bash

   python3 scripts/token_estimator.py --file skills/modular-skills/SKILL.md

Analyze all skills in a directory:

.. code-block:: bash

   python3 scripts/token_estimator.py --directory skills --include-dependencies

Output in JSON format:

.. code-block:: bash

   python3 scripts/token_estimator.py --directory skills --format json

Context Optimization
^^^^^^^^^^^^^^^^^^^^

Check if skills are optimized for context usage:

.. code-block:: bash

   python3 scripts/context_optimizer.py analyze skills/modular-skills/examples/basic-implementation

Get statistics for all skills:

.. code-block:: bash

   python3 scripts/context_optimizer.py stats skills

Skill Validation
^^^^^^^^^^^^^^^^

Validate a skill structure:

.. code-block:: bash

   python3 scripts/skill_analyzer.py --file my-skill/SKILL.md --verbose

Set a custom threshold for complexity:

.. code-block:: bash

   python3 scripts/skill_analyzer.py --directory skills --threshold 200

Using the CLI Framework
------------------------

Creating a New CLI Tool
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from abstract.cli_framework import AbstractCLI, CLIResult

   class MyToolCLI(AbstractCLI):
       def __init__(self):
           super().__init__(
               name="my-tool",
               description="My custom analysis tool",
               version="1.0.0"
           )

       def add_arguments(self, parser):
           parser.add_argument(
               "--input",
               type=Path,
               required=True,
               help="Input file to process"
           )

       def execute(self, args) -> CLIResult:
           try:
               # Your processing logic here
               result = process_file(args.input)
               return CLIResult(success=True, data=result)
           except Exception as e:
               return CLIResult(success=False, error=str(e))

   if __name__ == "__main__":
       cli_main(MyToolCLI)

Common Options
~~~~~~~~~~~~~~

All CLI tools support these common options:

- ``--format {text,json,summary,table}`` - Change output format
- ``--verbose`` - Increase verbosity (can be repeated)
- ``--quiet`` - Suppress non-essential output
- ``--config`` - Path to configuration file
- ``--project-root`` - Explicit project root directory
