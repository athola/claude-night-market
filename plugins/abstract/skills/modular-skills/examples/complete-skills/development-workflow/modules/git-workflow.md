---
name: git-workflow
description: Best practices for Git workflow including repository setup, branching strategies, and daily development practices
version: 1.0.0
created_by: abstract-examples
tags: [git, version-control, branching, workflow]
category: development
type: module
estimated_tokens: 120
dependencies: []
companion_skills: []
modules: []
tools:
  - setup-git
  - validate-branching
  - commit-validator

pattern: meta-skill
---

# Git Workflow

Comprehensive Git workflow management for teams, covering repository initialization, branching strategies, commit standards, and daily practices.

## Overview

Master Git collaboration with this complete workflow guide:

**🚀 Quick Start**: Get your team working efficiently in 10 minutes
- Set up repository with proper branching structure
- Configure commit message standards with hooks
- Start using feature branch workflow immediately

**📚 Progressive Learning**: Advance from basic to advanced Git practices
1. **Essentials** → Repository setup + basic branching + commit standards
2. **Team Workflow** → Feature branches + pull requests + code review
3. **Advanced** → Rebase + cherry-pick + hooks + performance optimization

**🎯 Use Case-Based**: Jump directly to your specific needs
- New repository? → Use repository initialization + branching strategy setup
- Team conflicts? → Apply conflict resolution + collaboration practices
- Production hotfix? → Follow hotfix workflow + merge procedures
- Performance issues? → Use large repository management + optimization techniques

## Repository Initialization

### Basic Repository Setup
```bash
# Initialize new repository
git init
echo "# Project Name" > README.md
git add README.md
git commit -m "Initial commit"

# Set up proper branching strategy
git checkout -b develop
```

### Remote Repository Setup
```bash
# Add remote and push initial structure
git remote add origin git@github.com:org/project.git
git push -u origin main
git push -u origin develop
```

## Branching Strategies

### GitFlow (Recommended for Teams)
```
main (production)
├── develop (integration)
├── feature/* (development)
├── release/* (staging)
└── hotfix/* (emergency fixes)
```

**Key Rules:**
- `main` is always production-ready
- `develop` integrates features for next release
- Features branch from `develop`, merge back to `develop`
- Releases branch from `develop`, merge to `main` and `develop`
- Hotfixes branch from `main`, merge to `main` and `develop`

### GitHub Flow (Simpler for Small Teams)
```
main (always deployable)
├── feature/* (development)
└── hotfix/* (emergency fixes)
```

**Key Rules:**
- `main` is always deployable
- Features branch from `main`, merge back via pull request
- Deploy after every merge to `main`

### Feature Branch Workflow
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication

# During development
git add .
git commit -m "feat(auth): implement user login"
git push origin feature/user-authentication

# Prepare for review
git checkout develop
git merge feature/user-authentication --no-ff
git push origin develop
```

## Commit Message Standards

### Conventional Commits Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependency updates

**Examples:**
```
feat(auth): add user authentication system

- Implement login endpoint with JWT tokens
- Add password reset functionality
- Update user model with auth fields

Closes #123, #124
```

### Breaking Changes
```
feat(api)!: change authentication header format

BREAKING CHANGE: Authentication now uses Bearer token format
instead of custom X-Auth-Token header. Update all API clients.
```

## Daily Git Workflow

### Start of Day Routine
```bash
# Sync with latest changes
git checkout main
git pull origin main
git checkout develop
git pull origin develop

# Start new work
git checkout -b feature/your-feature-name
```

### Development Routine
```bash
# Commit frequently with descriptive messages
git add .
git commit -m "feat(component): implement core functionality"

# Push regularly for backup and collaboration
git push origin feature/your-feature-name

# Check status often
git status
git log --oneline -5
```

### End of Day Routine
```bash
# Ensure everything is committed and pushed
git status
git add .
git commit -m "work: progress on feature X"
git push origin feature/your-feature-name
```

## Advanced Git Techniques

### Interactive Rebase for Cleanup
```bash
# Clean up commits before merging
git rebase -i HEAD~5

# Commands during interactive rebase:
# pick = use commit
# reword = edit commit message
# edit = edit commit content
# squash = merge with previous commit
# fixup = merge with previous, discarding message
# drop = remove commit
```

### Cherry-Pick for Selective Merges
```bash
# Copy specific commits between branches
git checkout develop
git cherry-pick abc1234  # Apply specific commit
```

### Stashing Work in Progress
```bash
# Save current work
git stash push -m "Work in progress on feature X"

# List stashes
git stash list

# Apply and remove stash
git stash pop stash@{0}

# Apply without removing
git stash apply stash@{0}
```

## Branch Management

### Cleanup Old Branches
```bash
# Delete merged local branches
git branch --merged develop | grep -v "develop" | xargs git branch -d

# Delete merged remote branches
git remote prune origin
```

### Protected Branches
**Configure in GitHub/GitLab:**
- Protect `main` and `develop` branches
- Require pull request reviews
- Require status checks to pass
- Require up-to-date branches before merging
- Include administrators as enforcement admins

## Git Hooks

### Pre-commit Hook Example
```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linting
npm run lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Run tests
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### Commit Message Hook
```bash
#!/bin/sh
# .git/hooks/commit-msg

# Validate commit message format
commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format. Use: type(scope): description"
    exit 1
fi
```

## Troubleshooting

### Undo Common Mistakes
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo last commit and preserve changes for later
git reset HEAD~1
git stash

# Fix last commit message
git commit --amend -m "New commit message"
```

### Merge Conflict Resolution
```bash
# When conflicts occur:
git status  # See conflicted files

# Edit files to resolve conflicts
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> branch-name

# Mark conflicts as resolved
git add conflicted-file.js

# Complete merge
git commit
```

## Team Collaboration

### Code Integration Process
1. **Feature Development**: Work on feature branches
2. **Pull Request**: Create PR from feature to develop
3. **Code Review**: Team reviews changes
4. **Testing**: Automated tests pass
5. **Integration**: Merge to develop
6. **Release**: Merge from develop to main

### Conflict Prevention
- Pull latest changes before starting work
- Commit frequently with logical chunks
- Use descriptive commit messages
- Review PRs promptly to minimize conflicts
- Use feature flags for large features

## Performance Optimization

### Large Repository Management
```bash
# Shallow clone for history (faster)
git clone --depth 1 git@github.com:org/repo.git

# Sparse checkout for specific directories
git config core.sparsecheckout true
echo "src/" >> .git/info/sparse-checkout
git read-tree -mu HEAD
```

### Gitignore Best Practices
```gitignore
# OS files
.DS_Store
Thumbs.db

# Dependencies
node_modules/
venv/
*.pyc

# Build artifacts
dist/
build/
target/

# IDE files
.vscode/
.idea/
*.swp
*.swo
```

## Integration with Development Tools

### IDE Integration
- Use Git integration features in VS Code, IntelliJ, etc.
- Configure line ending handling
- Set up Git user configuration

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Checkout repository
  uses: actions/checkout@v3
  with:
    fetch-depth: 0  # Full history for analysis

- name: Set up Git
  run: |
    git config --global user.name "CI Bot"
    git config --global user.email "ci@example.com"
```

## Monitoring and Analytics

### Repository Health Metrics
- Commit frequency and size
- Branch lifetime
- Merge conflict frequency
- Code review turnaround time
- Deployment frequency

### Git Statistics
```bash
# Commit statistics
git shortlog -sn
git log --stat --summary

# File change statistics
git log --name-only --pretty=format: | sort | uniq -c | sort -rg
```

This git workflow module provides comprehensive guidance for teams to establish consistent, efficient version control practices that scale with project complexity.
