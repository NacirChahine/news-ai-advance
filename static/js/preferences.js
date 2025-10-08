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
    // Use toast notifications instead of inline alerts
    if (success) {
      if (window.toast) {
        window.toast.success('Preferences saved automatically!');
      }
    } else {
      if (window.toast) {
        window.toast.error('Error saving preferences: ' + (message || 'Unknown error'));
      }
    }
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
  // Privacy preferences
  bindToggle('public_profile', 'public_profile');

  const misinformationAlertsCheckbox = document.getElementById('receive_misinformation_alerts');
  if (misinformationAlertsCheckbox && !misinformationAlertsCheckbox.disabled) {
    misinformationAlertsCheckbox.addEventListener('change', function() {
      autoSavePreference('receive_misinformation_alerts', this.checked);
    });
  }

  const sel = document.querySelector('select[name="political_filter"]');
  if (sel) sel.addEventListener('change', function() { autoSavePreference('political_filter', this.value); });

  // Profile picture upload
  const profilePictureInput = document.getElementById('profilePictureInput');
  const removePictureBtn = document.getElementById('removePictureBtn');
  const avatarPreview = document.getElementById('avatarPreview');

  function showUploadStatus(success, message) {
    // Use toast notifications instead of inline alerts
    if (window.toast) {
      if (success) {
        window.toast.success(message);
      } else {
        window.toast.error(message);
      }
    }
  }

  if (profilePictureInput) {
    profilePictureInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) return;

      // Validate file type
      const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
      if (!validTypes.includes(file.type)) {
        showUploadStatus(false, 'Please select a valid image file (JPG, PNG, or GIF)');
        profilePictureInput.value = '';
        return;
      }

      // Validate file size (2MB max)
      if (file.size > 2 * 1024 * 1024) {
        showUploadStatus(false, 'File size must be less than 2MB');
        profilePictureInput.value = '';
        return;
      }

      // Upload file
      const formData = new FormData();
      formData.append('profile_picture', file);

      fetch('/accounts/upload-profile-picture/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
        },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showUploadStatus(true, 'Profile picture updated successfully!');
          // Update preview
          if (avatarPreview.tagName === 'IMG') {
            avatarPreview.src = data.avatar_url + '?t=' + new Date().getTime();
          } else {
            // Replace letter avatar with image
            const img = document.createElement('img');
            img.id = 'avatarPreview';
            img.src = data.avatar_url;
            img.alt = 'Profile Picture';
            img.className = 'rounded-circle';
            img.style.cssText = 'width: 80px; height: 80px; object-fit: cover;';
            avatarPreview.replaceWith(img);
          }
          // Show remove button if not already visible
          if (removePictureBtn) {
            removePictureBtn.style.display = 'inline-block';
          } else {
            // Create remove button
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.id = 'removePictureBtn';
            btn.className = 'btn btn-sm btn-outline-danger mt-2';
            btn.innerHTML = '<i class="fas fa-trash me-1"></i>Remove Picture';
            profilePictureInput.parentElement.appendChild(btn);
            // Bind click event
            btn.addEventListener('click', removePicture);
          }
          // Reload page to update avatars in comments
          setTimeout(() => location.reload(), 1500);
        } else {
          showUploadStatus(false, data.error || 'Failed to upload profile picture');
        }
      })
      .catch(error => {
        showUploadStatus(false, 'Network error occurred');
      });
    });
  }

  function removePicture() {
    if (!confirm('Are you sure you want to remove your profile picture?')) return;

    fetch('/accounts/remove-profile-picture/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showUploadStatus(true, 'Profile picture removed successfully!');
        // Reload page to show letter avatar
        setTimeout(() => location.reload(), 1500);
      } else {
        showUploadStatus(false, data.error || 'Failed to remove profile picture');
      }
    })
    .catch(error => {
      showUploadStatus(false, 'Network error occurred');
    });
  }

  if (removePictureBtn) {
    removePictureBtn.addEventListener('click', removePicture);
  }
});

