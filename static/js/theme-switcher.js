/**
 * Enhanced Theme Switcher
 * Based on web.dev best practices
 * https://web.dev/patterns/theming/theme-switch
 */

const storageKey = 'theme-preference';

const getColorPreference = () => {
  if (localStorage.getItem(storageKey))
    return localStorage.getItem(storageKey);
  else
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
};

const setPreference = () => {
  localStorage.setItem(storageKey, theme.value);
  reflectPreference();
};

const reflectPreference = () => {
  document.firstElementChild.setAttribute('data-theme', theme.value);

  // Update Bootstrap theme attribute for compatibility
  document.documentElement.setAttribute('data-bs-theme', theme.value);

  const toggleBtn = document.querySelector('#theme-toggle');
  if (toggleBtn) {
    toggleBtn.setAttribute('aria-label', theme.value);
  }
};

const theme = {
  value: getColorPreference(),
};

// Set early so no page flashes / CSS is made aware
reflectPreference();

const onClick = () => {
  // Flip current value
  theme.value = theme.value === 'light' ? 'dark' : 'light';
  setPreference();
};

window.onload = () => {
  // Set on load so screen readers can see latest value on the button
  reflectPreference();

  // Now this script can find and listen for clicks on the control
  const toggleBtn = document.querySelector('#theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', onClick);
  }
};

// Sync with system changes
window
  .matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', ({matches: isDark}) => {
    theme.value = isDark ? 'dark' : 'light';
    setPreference();
  });

