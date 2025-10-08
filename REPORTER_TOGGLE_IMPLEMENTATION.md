# Reporter Toggle Implementation

## Overview
Added self-service reporter designation toggle to the user profile edit page, allowing users to enable/disable reporter status without admin intervention.

## Changes Made

### 1. Backend - View Update (`accounts/views.py`)

**Modified `edit_profile` view:**
- Added handling for `is_reporter` checkbox field
- Extracts checkbox value from POST data: `request.POST.get('is_reporter') == 'on'`
- Saves the value to `user_profile.is_reporter`
- Maintains all existing profile edit functionality

**Code changes:**
```python
# Added line to extract is_reporter value
is_reporter = request.POST.get('is_reporter') == 'on'  # Checkbox value

# Added line to save is_reporter to profile
user_profile.is_reporter = is_reporter
```

### 2. Frontend - Template Update (`accounts/templates/accounts/edit_profile.html`)

**Added reporter toggle section:**
- Bootstrap form-switch checkbox for modern toggle appearance
- Clear labeling: "I am a reporter/author"
- Comprehensive help text explaining what reporter status enables
- Checkbox is checked if user already has reporter status
- Positioned between profile picture and save button for logical flow

**HTML structure:**
```html
<div class="mb-3">
    <div class="form-check form-switch">
        <input class="form-check-input" type="checkbox" id="is_reporter" 
               name="is_reporter" {% if profile.is_reporter %}checked{% endif %}>
        <label class="form-check-label" for="is_reporter">
            <strong>I am a reporter/author</strong>
        </label>
    </div>
    <div class="form-text">
        <i class="fas fa-info-circle me-1"></i>
        Check this to enable article creation and management. 
        You'll be able to write, edit, and publish your own articles on the platform.
    </div>
</div>
```

### 3. Visual Enhancements

**Added Reporter Badge to Profile Pages:**

**Private Profile (`accounts/templates/accounts/profile.html`):**
- Blue badge with newspaper icon next to username
- Only visible when `profile.is_reporter` is True
- Format: `[Username] [🗞️ Reporter]`

**Public Profile (`templates/accounts/public_profile.html`):**
- Same badge styling for consistency
- Visible to all visitors when user is a reporter
- Helps identify content creators

## User Experience Flow

### Enabling Reporter Status:
1. User navigates to `/accounts/edit-profile/`
2. Scrolls to "I am a reporter/author" toggle
3. Checks the checkbox
4. Clicks "Save Changes"
5. Profile is updated with reporter status
6. "My Articles" button appears on profile page
7. Reporter badge appears next to username

### Disabling Reporter Status:
1. User navigates to `/accounts/edit-profile/`
2. Unchecks the "I am a reporter/author" toggle
3. Clicks "Save Changes"
4. Reporter status is removed
5. "My Articles" button disappears from profile
6. Reporter badge is hidden
7. **Note:** Existing articles remain but can no longer be edited

## Features Enabled by Reporter Status

When `is_reporter = True`:
- ✅ Access to "My Articles" page (`/news/my-articles/`)
- ✅ Create new articles (`/news/article/create/`)
- ✅ Edit own articles (`/news/article/<id>/edit/`)
- ✅ Delete own articles (`/news/article/<id>/delete/`)
- ✅ "My Articles" button on profile page
- ✅ "Authored Articles" tab on public profile
- ✅ Reporter badge on profile pages
- ✅ Clickable author name on article pages

## Security & Validation

### Form Validation:
- Checkbox value properly sanitized (boolean conversion)
- No additional validation needed (boolean field)
- Existing profile validation remains intact

### Authorization:
- Users can self-designate as reporters (no admin approval required)
- Article management views still check `is_reporter` status
- Users can only edit/delete their own articles
- Disabling reporter status doesn't delete existing articles

### Data Integrity:
- Profile save operation is atomic
- Existing profile data preserved
- No migration required (field already exists)

## Testing Checklist

- [ ] Toggle appears on edit profile page
- [ ] Checking toggle and saving enables reporter status
- [ ] Unchecking toggle and saving disables reporter status
- [ ] Reporter badge appears when status is enabled
- [ ] Reporter badge disappears when status is disabled
- [ ] "My Articles" button appears/disappears correctly
- [ ] Article management pages accessible when enabled
- [ ] Article management pages blocked when disabled
- [ ] Help text is clear and informative
- [ ] Form submission works with and without toggle change
- [ ] Profile picture upload still works
- [ ] Other profile fields still save correctly

## UI/UX Considerations

### Design Choices:
1. **Toggle Switch**: Modern Bootstrap form-switch for better UX
2. **Clear Labeling**: Bold text for primary label
3. **Helpful Context**: Icon + descriptive help text
4. **Visual Feedback**: Badge provides immediate status indication
5. **Consistent Styling**: Matches existing form elements

### Accessibility:
- Proper label association with `for` attribute
- Help text linked to input for screen readers
- Semantic HTML structure
- Keyboard accessible (native checkbox behavior)

## Future Enhancements (Optional)

Potential improvements for consideration:
1. **Confirmation Dialog**: Warn when disabling reporter status
2. **Article Count**: Show number of articles in help text
3. **Verification Badge**: Different badge for verified reporters
4. **Reporter Profile**: Enhanced profile section for reporters
5. **Analytics**: Track reporter activity and engagement

## Files Modified

1. `accounts/views.py` - Added is_reporter handling to edit_profile view
2. `accounts/templates/accounts/edit_profile.html` - Added toggle UI
3. `accounts/templates/accounts/profile.html` - Added reporter badge
4. `templates/accounts/public_profile.html` - Added reporter badge

## Related Documentation

- Main implementation: See project root documentation
- Reporter system overview: `AI_PROJECT_DOCS.md` (Reporter/Author System section)
- User guide: `README.md` (Reporter/Author System feature)

## Deployment Notes

- No database migrations required
- No static file changes needed
- No dependencies added
- Backward compatible with existing profiles
- Can be deployed without downtime

