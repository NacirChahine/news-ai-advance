document.addEventListener('DOMContentLoaded', function() {
  // Get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');
  const statusDiv = document.getElementById('save-status');
  const saveUrl = statusDiv ? (statusDiv.getAttribute('data-save-url') || '') : '';

  function showSaveStatus(success, message) {
    if (!statusDiv) return;
    statusDiv.className = success ? 'alert alert-success' : 'alert alert-danger';
    statusDiv.innerHTML = success ?
      '<i class="fas fa-check-circle me-2"></i>Preferences saved automatically!' :
      '<i class="fas fa-exclamation-triangle me-2"></i>Error saving preferences: ' + (message || '');
    statusDiv.classList.remove('d-none');
    setTimeout(() => statusDiv.classList.add('d-none'), 3000);
  }

  function autoSavePreference(fieldName, fieldValue) {
    if (!saveUrl) return;
    fetch(saveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({ field: fieldName, value: fieldValue })
    })
      .then(response => response.json())
      .then(data => showSaveStatus(data.success, data.error || data.message))
      .catch(() => showSaveStatus(false, 'Network error occurred'));
  }

  function bindToggle(id, fieldName) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', function() { autoSavePreference(fieldName, this.checked); });
  }

  bindToggle('enable_fact_check', 'enable_fact_check');
  bindToggle('enable_bias_analysis', 'enable_bias_analysis');
  bindToggle('enable_logical_fallacy_analysis', 'enable_logical_fallacy_analysis');
  bindToggle('enable_sentiment_analysis', 'enable_sentiment_analysis');
  bindToggle('enable_key_insights', 'enable_key_insights');
  bindToggle('enable_summary_display', 'enable_summary_display');
  // Comments preferences
  bindToggle('show_comments', 'show_comments');
  bindToggle('notify_on_comment_reply', 'notify_on_comment_reply');

  const misinformationAlertsCheckbox = document.getElementById('receive_misinformation_alerts');
  if (misinformationAlertsCheckbox && !misinformationAlertsCheckbox.disabled) {
    misinformationAlertsCheckbox.addEventListener('change', function() {
      autoSavePreference('receive_misinformation_alerts', this.checked);
    });
  }

  const sel = document.querySelector('select[name="political_filter"]');
  if (sel) sel.addEventListener('change', function() { autoSavePreference('political_filter', this.value); });
});

