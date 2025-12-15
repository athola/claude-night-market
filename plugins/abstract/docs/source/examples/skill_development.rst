Skill Development Examples
==========================

Creating a New Skill
--------------------

Basic Skill Structure
~~~~~~~~~~~~~~~~~~~~

Every skill should follow this structure:

.. code-block:: markdown

   ---
   name: my-skill
   description: Brief description of what this skill does
   category: utility
   version: 1.0.0
   ---

   # My Skill

   ## Overview

   Brief explanation of the skill's purpose and when to use it.

   ## Quick Start

   Simple steps to get started with the skill:

   1. First step
   2. Second step
   3. Third step

   ## Examples

   ### Basic Usage

   User: "I need to [task]"

   Response: [Expected response]

   ### Advanced Usage

   User: "I need to [complex task]"

   Response: [Expected response with detailed steps]

   ## Resources

   Links to additional resources, references, or related skills.

Modular Skills with Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For complex skills, use the modular structure:

.. code-block:: text

   my-skill/
   ├── SKILL.md           # Main skill definition
   ├── modules/           # Optional sub-modules
   │   ├── module1.md     # Module documentation
   │   └── module2.md     # Module documentation
   └── tools/             # Optional automation scripts
       ├── validate.py    # Validation script
       └── generate.py    # Generation script

Example: Data Analysis Skill
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: markdown

   ---
   name: data-analyzer
   description: Analyze and visualize data from various sources
   category: analysis
   version: 1.0.0
   dependencies: ["pandas", "matplotlib", "seaborn"]
   ---

   # Data Analyzer

   ## Overview

   Helps analyze and visualize data from CSV, JSON, and Excel files. Provides insights through statistical analysis and creates publication-ready charts.

   ## Quick Start

   1. Prepare your data file (CSV, JSON, or Excel)
   2. Specify the type of analysis you need
   3. Get insights and visualizations

   User: "Analyze this sales data and show trends"

   Response: I'll analyze your sales data to identify trends and create visualizations.

   [Continues with analysis steps...]

   ## Examples

   ### Sales Trend Analysis

   User: "I have sales_data.csv, show me monthly trends"

   Response: I'll analyze your sales data for monthly trends.

   ```python
   import pandas as pd
   import matplotlib.pyplot as plt

   # Load and process data
   df = pd.read_csv('sales_data.csv')
   df['date'] = pd.to_datetime(df['date'])
   monthly_sales = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()

   # Create visualization
   plt.figure(figsize=(12, 6))
   monthly_sales.plot(kind='line')
   plt.title('Monthly Sales Trends')
   plt.xlabel('Month')
   plt.ylabel('Sales Amount')
   plt.show()
   ```

   [Provides interpretation of results...]

   ### Statistical Summary

   User: "Give me a statistical summary of customer_data.json"

   Response: I'll provide a comprehensive statistical summary of your customer data.

   [Analyzes and presents key metrics...]

   ## Resources

   - Pandas documentation: https://pandas.pydata.org/docs/
   - Matplotlib gallery: https://matplotlib.org/stable/gallery/index.html
   - Statistical analysis guide: [link to guide]

Using the Tools Directory
------------------------

Validation Script Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Validate data format for analyzer skill."""

   import json
   import sys
   from pathlib import Path
   from abstract.cli_framework import AbstractCLI

   class DataValidatorCLI(AbstractCLI):
       def add_arguments(self, parser):
           parser.add_argument("data_file", type=Path, help="Data file to validate")

       def execute(self, args):
           file_path = args.data_file

           if not file_path.exists():
               return CLIResult(success=False, error=f"File not found: {file_path}")

           try:
               if file_path.suffix == ".csv":
                   # Validate CSV format
                   import pandas as pd
                   df = pd.read_csv(file_path)
                   issues = []
                   if df.empty:
                       issues.append("File is empty")
                   if df.isnull().any().any():
                       issues.append("Contains null values")
               elif file_path.suffix == ".json":
                   # Validate JSON format
                   with open(file_path) as f:
                       data = json.load(f)
                       issues = []
                       if not isinstance(data, list):
                           issues.append("JSON should be a list of records")

               return CLIResult(
                   success=len(issues) == 0,
                   data={"valid": len(issues) == 0, "issues": issues}
               )
           except Exception as e:
               return CLIResult(success=False, error=str(e))

   if __name__ == "__main__":
       cli_main(DataValidatorCLI)

Best Practices
--------------

Token Optimization
~~~~~~~~~~~~~~~~~~

1. **Use Progressive Disclosure**:
   - Start with overview
   - Provide quick steps
   - Add detailed examples in sections
   - Keep code blocks concise

2. **Modularize Large Skills**:
   - Break skills >2000 tokens into modules
   - Use tools/ directory for complex logic
   - Reference external documentation

3. **Include Examples**:
   - Always provide 2-3 concrete examples
   - Show expected user input and Claude response
   - Include code blocks where relevant

Error Handling
~~~~~~~~~~~~

Create robust skills that handle errors gracefully:

.. code-block:: markdown

   User: "Process this malformed data file"

   Response: I notice the data file has some issues. Let me help you fix them:

   1. **Missing headers**: The CSV file is missing column headers
   2. **Extra commas**: There are trailing commas on some lines
   3. **Date format**: Inconsistent date formats

   Here's how to fix your file:

   [Provides specific fixes...]

   Would you like me to process the corrected file?

Testing Your Skill
~~~~~~~~~~~~~~~~~

Use the built-in validation tools:

.. code-block:: bash

   # Check token usage
   python3 scripts/token_estimator.py --file my-skill/SKILL.md

   # Validate structure
   python3 scripts/skill_analyzer.py --file my-skill/SKILL.md

   # Check for common issues
   python3 scripts/abstract_validator.py --skill-path my-skill/SKILL.md
