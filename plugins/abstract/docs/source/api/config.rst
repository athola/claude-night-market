Configuration
=============

.. automodule:: abstract.config
   :members:
   :member-order: bysource
   :show-inheritance:
   :special-members: __init__

AbstractConfig
--------------

.. autoclass:: abstract.config.AbstractConfig
   :members:
   :inherited-members:
   :show-inheritance:

Example Usage
------------

.. code-block:: python

   from abstract.config import AbstractConfig

   # Load from file
   config = AbstractConfig.from_yaml("config.yaml")

   # Create default config
   config = AbstractConfig()

   # Access configuration
   print(config.skills_dir)
   print(config.optimization_settings)

   # Update settings
   config.update({
       "skills_dir": "custom/skills",
       "token_limit": 4000
   })
