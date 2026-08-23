---
schema: nightshift/tasks@1
item: NS-000
tasks:
  - id: T1
    kind: red
    title: A failing check that proves the defect exists
    files: [path/to/test_file.py]
    change: What to add, specifically enough to act on without asking.
    evidence:
      command: uv run pytest path/to/test_file.py::test_name -q
      expect: fail
      match: "1 failed"
    depends_on: []
  - id: T2
    kind: green
    title: The smallest change that turns T1 green
    files: [path/to/source.py]
    change: What to change.
    evidence:
      command: uv run pytest path/to/test_file.py::test_name -q
      expect: pass
      match: "1 passed"
    depends_on: [T1]
---
