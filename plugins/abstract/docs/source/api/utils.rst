Utilities
=========

.. automodule:: abstract.utils
   :members:
   :member-order: bysource
   :show-inheritance:
   :special-members: __init__

Key Functions
-------------

File Operations
~~~~~~~~~~~~~~~

.. autofunction:: abstract.utils.find_project_root

.. autofunction:: abstract.utils.load_config_with_defaults

Frontmatter Operations
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: abstract.utils.parse_yaml_frontmatter

.. autofunction:: abstract.utils.extract_frontmatter

.. autofunction:: abstract.utils.validate_frontmatter

Token Analysis
~~~~~~~~~~~~~~

.. autofunction:: abstract.utils.estimate_tokens

.. autofunction:: abstract.utils.analyze_token_components

.. autofunction:: abstract.utils.count_tokens_detailed

Skill Analysis
~~~~~~~~~~~~~~

.. autofunction:: abstract.utils.count_sections

.. autofunction:: abstract.utils.extract_code_blocks

.. autofunction:: abstract.utils.extract_dependencies

.. autofunction:: abstract.utils.find_dependency_file

Example Usage
------------

.. code-block:: python

   from abstract.utils import (
       parse_yaml_frontmatter,
       estimate_tokens,
       find_project_root
   )

   # Parse frontmatter from a skill file
   with open("my-skill/SKILL.md") as f:
       content = f.read()

   frontmatter = parse_yaml_frontmatter(content)
   print(f"Skill name: {frontmatter.get('name')}")

   # Estimate tokens
   tokens = estimate_tokens(content)
   print(f"Estimated tokens: {tokens}")

   # Find project root
   root = find_project_root(Path("my-skill/SKILL.md"))
   print(f"Project root: {root}")
