Deprecation Policy
==================

This document outlines the deprecation policy for the Abstract plugin infrastructure.

Current Status
--------------

**No APIs are currently deprecated.**

This policy is in place for future reference when deprecation becomes necessary.

General Principles
-----------------

When we deprecate APIs or features:

1. **Clear Communication**: Users are informed well in advance
2. **Migration Path**: Alternative solutions are provided
3. **Timeline**: Sufficient time is given for migration
4. **Documentation**: Guides and examples are provided

Deprecation Process
-------------------

### 1. Identification

An API or feature may be deprecated when:

- It has a better alternative
- It's no longer needed
- It causes maintenance issues
- It has security vulnerabilities
- It doesn't align with project goals

### 2. Announcement

Deprecation is announced through:

- **Code warnings**: Using the deprecated API triggers a warning
- **Documentation**: Clearly marked in API docs
- **Changelog**: Documented in release notes
- **Issue tracking**: Tracked in a GitHub issue

Example deprecation warning:

.. code-block:: python

   import warnings

   def old_api():
       warnings.warn(
           "old_api() is deprecated and will be removed in v2.0.0. "
           "Use new_api() instead. "
           "See migration guide: docs/migrations/v2.md",
           DeprecationWarning,
           stacklevel=2
       )
       # ... implementation ...

### 3. Timeline

Deprecation follows SemVer timelines:

- **Patch Version**: Announce deprecation, no removal
- **Minor Version**: Continue supporting with warnings
- **Major Version**: Remove deprecated APIs

Example Timeline
~~~~~~~~~~~~~~~~~

- **v1.1.0**: Deprecate ``old_api()`` with warnings
- **v1.1.x to v1.2.x**: Continue supporting with warnings
- **v2.0.0**: Remove ``old_api()`` completely

### 4. Migration Support

For each deprecation, we provide:

- **Migration Guide**: Step-by-step instructions
- **Compatibility Checker**: Script to identify deprecated usage
- **Examples**: Before/after code comparisons
- **Support**: Help during migration period

Types of Deprecation
--------------------

### API Deprecation
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Deprecated API
   @deprecated(
       version="1.2.0",
       removal_version="2.0.0",
       alternative="new_class.NewMethod()",
       reason="More efficient implementation"
   )
   class OldClass:
       pass

   # New API
   class NewClass:
       def NewMethod(self):
           pass

### CLI Argument Deprecation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Old argument (deprecated)
   python3 scripts/tool.py --old-flag

   # Warning: --old-flag is deprecated, use --new-flag instead
   # Will be removed in v2.0.0

   # New argument
   python3 scripts/tool.py --new-flag

### Configuration Deprecation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Old configuration (deprecated)
   old_setting: true

   # Warning: old_setting is deprecated, use new_setting instead
   # Will be removed in v2.0.0

   # New configuration
   new_setting: true

### Module Deprecation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Old import (deprecated)
   from abstract.old_module import OldClass

   # Warning: abstract.old_module is deprecated
   # Use abstract.new_module instead
   # Will be removed in v2.0.0

   # New import
   from abstract.new_module import NewClass

Handling Deprecated Features
---------------------------

### As a User

When you see deprecation warnings:

1. **Don't Ignore**: Update your code promptly
2. **Check Migration Guide**: Follow recommended alternatives
3. **Test Thoroughly**: validate new implementation works
4. **Pin Versions**: If unable to update immediately

.. code-block:: toml

   # Pin to avoid deprecated APIs
   abstract = "==1.1.0"

### As a Developer

When introducing deprecation:

1. **Use ``@deprecated`` decorator** for clear documentation
2. **Add ``warnings.warn()`` with proper message**
3. **Update documentation** immediately
4. **Create migration guide** before first deprecated release

Deprecation Decorator
--------------------

Use the provided decorator for consistent deprecation:

.. code-block:: python

   from abstract.utils import deprecated

   @deprecated(
       version="1.2.0",
       removal_version="2.0.0",
       alternative="new_function()",
       reason="More efficient implementation"
   )
   def old_function():
       """Deprecated: Use new_function() instead."""
       warnings.warn(
           "old_function() is deprecated since v1.2.0 "
           "and will be removed in v2.0.0. "
           "Use new_function() instead.",
           DeprecationWarning,
           stacklevel=2
       )
       return new_function()

Emergency Deprecation
--------------------

In rare cases (security issues, critical bugs), APIs may be deprecated and removed in the same major version:

- Clearly marked as emergency deprecation
- Immediate migration required
- Extended support in LTS versions if available
- Multiple communication channels used

Future Considerations
--------------------

As Abstract evolves, we may consider:

1. **LTS Versions**: Long-term support for specific versions
2. **Compatibility Packages**: Separate package for legacy support
3. **Gradual Migration**: Tools to help migrate large codebases
4. **Community Feedback**: Adjust policy based on user needs

Any changes to this deprecation policy will be:
- Announced well in advance
- Documented thoroughly
- Implemented gradually
- Open to community feedback
