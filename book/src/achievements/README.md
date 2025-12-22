# Achievement System

Track your learning progress through the Claude Night Market documentation.

## How It Works

As you explore the documentation, complete tutorials, and try plugins, you earn achievements. Progress is saved in your browser's local storage.

## Your Progress

<div id="achievement-dashboard">
  <div class="progress-summary">
    <span id="total-achievements">0</span> / <span id="max-achievements">15</span> achievements unlocked
  </div>
  <div class="progress-bar">
    <div id="progress-fill" class="progress-fill"></div>
  </div>
</div>

## Available Achievements

### Getting Started

| Achievement | Description | Status |
|-------------|-------------|--------|
| Marketplace Pioneer | Add the Night Market marketplace | <span class="achievement-status" data-achievement="marketplace-added"></span> |
| Skill Apprentice | Use your first skill | <span class="achievement-status" data-achievement="first-skill"></span> |
| PR Pioneer | Prepare your first pull request | <span class="achievement-status" data-achievement="first-pr"></span> |

### Documentation Explorer

| Achievement | Description | Status |
|-------------|-------------|--------|
| Plugin Explorer | Read all plugin documentation pages | <span class="achievement-status" data-achievement="plugin-explorer"></span> |
| Domain Master | Use all domain specialist plugins | <span class="achievement-status" data-achievement="domain-master"></span> |

### Tutorial Completion

| Achievement | Description | Status |
|-------------|-------------|--------|
| Cache Commander | Complete the Cache Modes tutorial | <span class="achievement-status" data-achievement="cache-modes-complete"></span> |
| Semantic Scholar | Complete the Embedding Upgrade tutorial | <span class="achievement-status" data-achievement="embedding-upgrade-complete"></span> |
| Knowledge Curator | Complete the Curation tutorial | <span class="achievement-status" data-achievement="curation-complete"></span> |
| Tutorial Master | Complete all tutorials | <span class="achievement-status" data-achievement="tutorial-master"></span> |

### Plugin Mastery

| Achievement | Description | Status |
|-------------|-------------|--------|
| Foundation Builder | Install all foundation layer plugins | <span class="achievement-status" data-achievement="foundation-complete"></span> |
| Utility Expert | Install all utility layer plugins | <span class="achievement-status" data-achievement="utility-complete"></span> |
| Full Stack | Install all plugins | <span class="achievement-status" data-achievement="full-stack"></span> |

### Advanced

| Achievement | Description | Status |
|-------------|-------------|--------|
| Spec Master | Complete a full spec-kit workflow | <span class="achievement-status" data-achievement="spec-master"></span> |
| Review Expert | Complete a full pensive review | <span class="achievement-status" data-achievement="review-expert"></span> |
| Palace Architect | Build your first memory palace | <span class="achievement-status" data-achievement="palace-architect"></span> |

## Reset Progress

<button id="reset-achievements" class="reset-button">Reset All Achievements</button>

*Warning: This cannot be undone.*

## Achievement Tiers

| Tier | Achievements | Badge |
|------|-------------|-------|
| Bronze | 1-5 | Night Market Visitor |
| Silver | 6-10 | Night Market Regular |
| Gold | 11-14 | Night Market Expert |
| Platinum | 15 | Night Market Master |

<div id="current-tier" class="tier-badge"></div>
