---
name: protect-env-files
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.env(\.|$)
  - field: new_text
    operator: regex_match
    pattern: (API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)\s*=
---

🔐 **Sensitive credential detected in .env file!**

You're adding credentials to an environment file.

**Security checklist:**
- [ ] File is in `.gitignore`
- [ ] Not using real production secrets
- [ ] Using placeholder values for examples
- [ ] Team knows not to commit this file

**Best practices:**
```bash
# In .gitignore
.env
.env.local
.env.*.local

# In .env.example (commit this)
API_KEY=your_api_key_here
SECRET=your_secret_here

# In .env (never commit)
API_KEY=actual_key_value
SECRET=actual_secret_value
```

**Verify .gitignore:**
```bash
git check-ignore .env
# Should output: .env
```
