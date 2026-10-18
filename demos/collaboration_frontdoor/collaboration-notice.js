(() => {
  'use strict';
  const version = 'CC-INTRO-2026-10-18-v1';
  const key = 'civic-continuum-notice-seen';
  const dialog = document.querySelector('#collaboration-notice');
  let previousFocus = null;
  const open = () => {
    if (!dialog || dialog.open) return;
    previousFocus = document.activeElement;
    dialog.showModal();
  };
  const rememberSeen = () => {
    try { localStorage.setItem(key, version); } catch (_) { /* Browsing still works. */ }
  };
  document.querySelectorAll('[data-open-collaboration]').forEach(button => button.addEventListener('click', open));
  if (dialog) {
    dialog.querySelectorAll('[data-close-notice]').forEach(button => button.addEventListener('click', () => dialog.close()));
    dialog.addEventListener('close', () => {
      rememberSeen();
      if (previousFocus && typeof previousFocus.focus === 'function') previousFocus.focus();
    });
    let seen = false;
    try { seen = localStorage.getItem(key) === version; } catch (_) { /* Show notice if storage is unavailable. */ }
    if (!seen) open();
  }
  const copyButton = document.querySelector('#copy-greeting');
  if (copyButton) copyButton.addEventListener('click', async () => {
    const text = document.querySelector('#standard-greeting').textContent.trim();
    const status = document.querySelector('#copy-status');
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = 'Greeting copied. Personalize the opening before sending.';
    } catch (_) {
      status.textContent = 'Copy is unavailable in this browser. Select and copy the greeting above.';
    }
  });
})();
