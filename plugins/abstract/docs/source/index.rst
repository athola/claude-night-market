Abstract Plugin Infrastructure
=============================

Meta-skills framework for Claude Code with modular design patterns and evaluation tools.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index
   examples/index
   contributing
   changelog
   governance
   api-stability
   deprecation

Features
--------

* **Modular Skills**: Reusable skill components with module support
* **Quality Tools**: Automated skill evaluation and analysis
* **Token Optimization**: Context window management strategies
* **Centralized Utilities**: Shared Python package eliminates code duplication

Installation
------------

Add this plugin to your Claude Code marketplace by adding the following to your ``marketplace.json``:

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
