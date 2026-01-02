// Claude Night Market - Achievement System
// localStorage-based progress tracking

(function() {
  'use strict';

  const STORAGE_KEY = 'claude-night-market-achievements';
  const VERSION = '1.0.0';

  // Achievement definitions
  const ACHIEVEMENTS = {
    // Getting Started
    'marketplace-added': {
      name: 'Marketplace Pioneer',
      description: 'Add the Night Market marketplace',
      category: 'getting-started'
    },
    'first-skill': {
      name: 'Skill Apprentice',
      description: 'Use your first skill',
      category: 'getting-started'
    },
    'first-pr': {
      name: 'PR Pioneer',
      description: 'Prepare your first pull request',
      category: 'getting-started'
    },

    // Documentation Explorer
    'plugin-explorer': {
      name: 'Plugin Explorer',
      description: 'Read all plugin documentation pages',
      category: 'documentation'
    },
    'domain-master': {
      name: 'Domain Master',
      description: 'Use all domain specialist plugins',
      category: 'documentation'
    },

    // Tutorial Completion
    'cache-modes-complete': {
      name: 'Cache Commander',
      description: 'Complete the Cache Modes tutorial',
      category: 'tutorials'
    },
    'embedding-upgrade-complete': {
      name: 'Semantic Scholar',
      description: 'Complete the Embedding Upgrade tutorial',
      category: 'tutorials'
    },
    'curation-complete': {
      name: 'Knowledge Curator',
      description: 'Complete the Curation tutorial',
      category: 'tutorials'
    },
    'tutorial-master': {
      name: 'Tutorial Master',
      description: 'Complete all tutorials',
      category: 'tutorials'
    },

    // Plugin Mastery
    'foundation-complete': {
      name: 'Foundation Builder',
      description: 'Install all foundation layer plugins',
      category: 'plugins'
    },
    'utility-complete': {
      name: 'Utility Expert',
      description: 'Install all utility layer plugins',
      category: 'plugins'
    },
    'full-stack': {
      name: 'Full Stack',
      description: 'Install all plugins',
      category: 'plugins'
    },

    // Advanced
    'spec-master': {
      name: 'Spec Master',
      description: 'Complete a full spec-kit workflow',
      category: 'advanced'
    },
    'review-expert': {
      name: 'Review Expert',
      description: 'Complete a full pensive review',
      category: 'advanced'
    },
    'palace-architect': {
      name: 'Palace Architect',
      description: 'Build your first memory palace',
      category: 'advanced'
    }
  };

  // Load achievements from localStorage
  function loadAchievements() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.version === VERSION) {
          return data.achievements || {};
        }
      }
    } catch (e) {
      console.warn('Failed to load achievements:', e);
    }
    return {};
  }

  // Save achievements to localStorage
  function saveAchievements(achievements) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: VERSION,
        achievements: achievements,
        lastUpdated: new Date().toISOString()
      }));
    } catch (e) {
      console.warn('Failed to save achievements:', e);
    }
  }

  // Unlock an achievement
  function unlockAchievement(id) {
    const achievements = loadAchievements();
    if (!achievements[id]) {
      achievements[id] = {
        unlockedAt: new Date().toISOString()
      };
      saveAchievements(achievements);
      showUnlockNotification(id);
    }
  }

  // Check if achievement is unlocked
  function isUnlocked(id) {
    const achievements = loadAchievements();
    return !!achievements[id];
  }

  // Show unlock notification using safe DOM methods
  function showUnlockNotification(id) {
    const achievement = ACHIEVEMENTS[id];
    if (!achievement) return;

    // Create notification container
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';

    // Create content container
    const content = document.createElement('div');
    content.className = 'achievement-notification-content';

    // Create star span
    const star = document.createElement('span');
    star.className = 'achievement-star';
    star.textContent = '\u2605'; // Unicode star character

    // Create text container
    const textContainer = document.createElement('div');

    // Create title
    const title = document.createElement('strong');
    title.textContent = 'Achievement Unlocked!';

    // Create achievement name
    const name = document.createElement('p');
    name.textContent = achievement.name;

    // Assemble the notification
    textContainer.appendChild(title);
    textContainer.appendChild(name);
    content.appendChild(star);
    content.appendChild(textContainer);
    notification.appendChild(content);

    // Add notification styles if not present
    if (!document.getElementById('achievement-notification-styles')) {
      const style = document.createElement('style');
      style.id = 'achievement-notification-styles';
      style.textContent = [
        '.achievement-notification {',
        '  position: fixed;',
        '  top: 20px;',
        '  right: 20px;',
        '  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);',
        '  color: white;',
        '  padding: 1rem 1.5rem;',
        '  border-radius: 8px;',
        '  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);',
        '  z-index: 10000;',
        '  animation: slide-in 0.5s ease-out, fade-out 0.5s ease-in 3s forwards;',
        '}',
        '.achievement-notification-content {',
        '  display: flex;',
        '  align-items: center;',
        '  gap: 0.75rem;',
        '}',
        '.achievement-star {',
        '  font-size: 2rem;',
        '  animation: star-spin 1s ease-out;',
        '}',
        '@keyframes slide-in {',
        '  from { transform: translateX(100%); opacity: 0; }',
        '  to { transform: translateX(0); opacity: 1; }',
        '}',
        '@keyframes fade-out {',
        '  from { opacity: 1; }',
        '  to { opacity: 0; }',
        '}'
      ].join('\n');
      document.head.appendChild(style);
    }

    document.body.appendChild(notification);
    setTimeout(function() {
      notification.remove();
    }, 3500);
  }

  // Count unlocked achievements
  function countUnlocked() {
    return Object.keys(loadAchievements()).length;
  }

  // Get current tier
  function getCurrentTier() {
    var count = countUnlocked();
    if (count >= 15) return { name: 'Platinum', className: 'platinum', title: 'Night Market Master' };
    if (count >= 11) return { name: 'Gold', className: 'gold', title: 'Night Market Expert' };
    if (count >= 6) return { name: 'Silver', className: 'silver', title: 'Night Market Regular' };
    if (count >= 1) return { name: 'Bronze', className: 'bronze', title: 'Night Market Visitor' };
    return { name: 'None', className: '', title: 'New Explorer' };
  }

  // Update achievement status elements
  function updateStatusElements() {
    var statusElements = document.querySelectorAll('.achievement-status');
    for (var i = 0; i < statusElements.length; i++) {
      var el = statusElements[i];
      var id = el.dataset.achievement;
      if (isUnlocked(id)) {
        el.classList.add('unlocked');
      }
    }

    var checkboxElements = document.querySelectorAll('.achievement-checkbox');
    for (var j = 0; j < checkboxElements.length; j++) {
      var checkbox = checkboxElements[j];
      var tutorialId = checkbox.dataset.tutorial;
      if (isUnlocked(tutorialId + '-complete')) {
        checkbox.classList.add('complete');
      }
    }
  }

  // Update dashboard
  function updateDashboard() {
    var total = document.getElementById('total-achievements');
    var max = document.getElementById('max-achievements');
    var fill = document.getElementById('progress-fill');
    var tierBadge = document.getElementById('current-tier');

    if (total) total.textContent = countUnlocked();
    if (max) max.textContent = Object.keys(ACHIEVEMENTS).length;
    if (fill) fill.style.width = (countUnlocked() / Object.keys(ACHIEVEMENTS).length * 100) + '%';

    if (tierBadge) {
      var tier = getCurrentTier();
      tierBadge.className = 'tier-badge ' + tier.className;
      tierBadge.textContent = tier.title;
    }
  }

  // Handle achievement unlocks from page content
  function processPageUnlocks() {
    var unlockElements = document.querySelectorAll('.achievement-unlock');
    for (var i = 0; i < unlockElements.length; i++) {
      var el = unlockElements[i];
      var id = el.dataset.achievement;
      if (id && !isUnlocked(id)) {
        unlockAchievement(id);
      }
    }
  }

  // Handle reset button
  function setupResetButton() {
    var resetBtn = document.getElementById('reset-achievements');
    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to reset all achievements? This cannot be undone.')) {
          localStorage.removeItem(STORAGE_KEY);
          location.reload();
        }
      });
    }
  }

  // Track page views for plugin-explorer achievement
  function trackPageView() {
    var path = window.location.pathname;

    // Track plugin page views
    var pluginPages = [
      'abstract', 'imbue', 'sanctum', 'leyline', 'conserve', 'conjure',
      'archetypes', 'pensive', 'parseltongue', 'memory-palace', 'spec-kit', 'minister'
    ];

    var viewedPlugins = JSON.parse(localStorage.getItem('viewed-plugins') || '[]');

    for (var i = 0; i < pluginPages.length; i++) {
      var plugin = pluginPages[i];
      if (path.indexOf('/plugins/' + plugin) !== -1) {
        if (viewedPlugins.indexOf(plugin) === -1) {
          viewedPlugins.push(plugin);
          localStorage.setItem('viewed-plugins', JSON.stringify(viewedPlugins));
        }
      }
    }

    // Check if all plugins viewed
    if (viewedPlugins.length >= pluginPages.length && !isUnlocked('plugin-explorer')) {
      unlockAchievement('plugin-explorer');
    }
  }

  // Initialize
  function init() {
    updateStatusElements();
    updateDashboard();
    processPageUnlocks();
    setupResetButton();
    trackPageView();
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose API for manual unlocks
  window.NightMarketAchievements = {
    unlock: unlockAchievement,
    isUnlocked: isUnlocked,
    count: countUnlocked,
    getTier: getCurrentTier,
    ACHIEVEMENTS: ACHIEVEMENTS
  };
})();
