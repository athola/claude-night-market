---
name: warn-large-commits
enabled: true
event: bash
action: warn
conditions:
  - field: command
    operator: contains
    pattern: git add
  - field: command
    operator: regex_match
    pattern: \.(zip|tar|gz|mp4|avi|mov)$
---

**Large binary file detected in git add!**

You're adding a large binary file (.zip, .tar, .mp4, etc.)

**Problems:**
- Bloats repository size permanently
- Slows down clones
- Binary files can't be diffed
- Wastes team bandwidth

**Better alternatives:**
```bash
# Add to .gitignore
echo "*.zip" >> .gitignore
echo "*.tar.gz" >> .gitignore

# Use Git LFS for large files
git lfs track "*.mp4"
git lfs track "*.zip"

# Or use external storage
# - S3/Cloud storage
# - Package registries
# - Artifact repositories
```
