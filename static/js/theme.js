/* News Advance theme toggling and auto-detection */
(function () {
  const PREF_KEY = 'na-theme'; // 'light' | 'dark'
  const root = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');
  const media = window.matchMedia('(prefers-color-scheme: dark)');

  let userSet = false; // whether user has explicit preference

  const getStored = () => localStorage.getItem(PREF_KEY);
  const setStored = (val) => localStorage.setItem(PREF_KEY, val);

  function currentTheme() {
    return root.getAttribute('data-theme');
  }

  function updateToggleIcon(theme) {
    if (!toggleBtn) return;
    const icon = toggleBtn.querySelector('i');
    if (!icon) return;
    // Show icon for the theme the user would switch TO
    if (theme === 'dark') {
      icon.className = 'fas fa-sun';
      toggleBtn.setAttribute('aria-label', 'Switch to light theme');
      toggleBtn.setAttribute('title', 'Switch to light theme');
      toggleBtn.setAttribute('aria-pressed', 'true');
    } else {
      icon.className = 'fas fa-moon';
      toggleBtn.setAttribute('aria-label', 'Switch to dark theme');
      toggleBtn.setAttribute('title', 'Switch to dark theme');
      toggleBtn.setAttribute('aria-pressed', 'false');
    }
  }

  function withSmoothTransition(fn) {
    // Temporarily enable smooth transitions for theme changes
    const prev = root.style.transition;
    root.style.transition = 'background-color 300ms ease, color 300ms ease';
    document.body.style.transition = 'background-color 300ms ease, color 300ms ease';
    try { fn(); } finally {
      window.setTimeout(() => {
        root.style.transition = prev || '';
        document.body.style.transition = '';
      }, 350);
    }
  }

  function applyTheme(theme) {
    withSmoothTransition(() => {
      root.setAttribute('data-theme', theme);
      updateToggleIcon(theme);
    });
  }

  function initTheme() {
    const stored = getStored();
    if (stored === 'light' || stored === 'dark') {
      userSet = true;
      applyTheme(stored);
    } else {
      // No stored preference: follow system
      const system = media.matches ? 'dark' : 'light';
      applyTheme(system);
    }
  }

  // Toggle handler
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      userSet = true;
      setStored(next);
      applyTheme(next);
    });
  }

  // Reflect system changes when user hasn't set a preference
  media.addEventListener('change', (e) => {
    if (!userSet) applyTheme(e.matches ? 'dark' : 'light');
  });

  // Initialize
  initTheme();
})();

