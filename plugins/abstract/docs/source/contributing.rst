Contributing
============

We welcome contributions to the Abstract plugin infrastructure!

Getting Started
---------------

1. **Fork the Repository**

   .. code-block:: bash

      git clone https://github.com/yourusername/abstract.git
      cd abstract

2. **Set Up Development Environment**

   .. code-block:: bash

      uv sync --dev
      make install-hooks

3. **Create a Feature Branch**

   .. code-block:: bash

      git checkout -b feature/my-new-feature

4. **Make Your Changes**

   - Write code
   - Add tests
   - Update documentation

5. **Run Tests**

   .. code-block:: bash

      make test

6. **Submit a Pull Request**

Development Guidelines
----------------------

Code Style
~~~~~~~~~~~

We use ruff for code formatting and linting:

.. code-block:: bash

   make format    # Format code
   make lint      # Check linting

Type Checking
~~~~~~~~~~~~~

All new code should pass mypy type checking:

.. code-block:: bash

   make check-types

Testing
~~~~~~~

- Write tests for new functionality
- validate all tests pass: ``make test``
- Aim for high test coverage

Documentation
~~~~~~~~~~~~~

- Update relevant documentation
- Add examples for new features
- Update API docs if adding public methods

Commit Messages
~~~~~~~~~~~~~~~

Follow conventional commit format:

.. code-block:: text

   type(scope): description

   feat(cli): add new output format option
   fix(parser): handle missing files gracefully
   docs(api): update token estimator documentation

Types:
- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation
- ``style``: Formatting
- ``refactor``: Refactoring
- ``test``: Tests
- ``chore``: Maintenance

Contributor License Agreement
----------------------------~

By contributing, you agree that your contributions will be licensed under the same license as the project.

Reporting Issues
----------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, please include:

- Python version
- OS information
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

Feature Requests
~~~~~~~~~~~~~~~~

For feature requests:

- Describe the use case
- Explain why it's needed
- Suggest a possible implementation
- Consider if it fits the project scope

Security Issues
~~~~~~~~~~~~~~~

For security issues, please email: alexthola@gmail.com

Project Structure
----------------

Understanding the Codebase
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   abstract/
   ├── skills/                    # Meta-skills
   │   ├── modular-skills/        # Modular design patterns
   │   └── skills-eval/           # Evaluation tools
   ├── scripts/                   # Utility scripts
   │   ├── token_estimator.py
   │   ├── context_optimizer.py
   │   ├── skill_analyzer.py
   │   └── abstract_validator.py
   ├── src/abstract/              # Python package
   │   ├── __init__.py
   │   ├── cli.py                # Main CLI entry
   │   ├── cli_framework.py       # CLI base classes
   │   ├── config.py              # Configuration
   │   ├── frontmatter.py         # Frontmatter processing
   │   ├── utils.py               # Utilities
   │   └── skills_eval.py         # Evaluation logic
   └── tests/                     # Test suite

Adding New Skills
~~~~~~~~~~~~~~~~~

1. Create a new directory in ``skills/``
2. Add a ``SKILL.md`` file with proper frontmatter
3. Follow the progressive disclosure structure
4. Test with the validation tools

Adding New Scripts
~~~~~~~~~~~~~~~~~~

1. Add to ``scripts/`` directory
2. Use the AbstractCLI base class
3. Include proper error handling
4. Add tests in ``tests/``

Release Process
---------------

Versioning
~~~~~~~~~~~

We follow Semantic Versioning (semver):

- ``MAJOR.MINOR.PATCH``
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

Release Checklist
~~~~~~~~~~~~~~~~~

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Run full test suite
4. Update documentation
5. Create a git tag
6. Build and publish if needed

Community
----------

Code of Conduct
~~~~~~~~~~~~~~~

Be respectful and constructive. We're here to learn and build together.

Getting Help
~~~~~~~~~~~~

- Create an issue for questions
- Join discussions in existing issues
- Check documentation first

Recognition
~~~~~~~~~~~

All contributors are recognized in:
- ``AUTHORS`` file
- Release notes
- Commit history

Thank you for contributing!
