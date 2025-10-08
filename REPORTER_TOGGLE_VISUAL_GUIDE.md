# Reporter Toggle - Visual Guide

## User Interface Overview

### 1. Edit Profile Page (`/accounts/edit-profile/`)

The reporter toggle appears in the profile edit form between the profile picture field and the save button:

```
┌─────────────────────────────────────────────────────────────┐
│ Edit Profile                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Username                                                     │
│ [username_here]                    (disabled)                │
│ Username cannot be changed                                   │
│                                                              │
│ Email                                                        │
│ [user@example.com]                                          │
│                                                              │
│ First Name                    Last Name                     │
│ [John]                        [Doe]                         │
│                                                              │
│ Bio                                                          │
│ [Text area for bio...]                                      │
│                                                              │
│ Profile Picture                                              │
│ [Choose File] No file chosen                                │
│                                                              │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ 🔘 I am a reporter/author                           │    │
│ │ ℹ️  Check this to enable article creation and       │    │
│ │    management. You'll be able to write, edit, and   │    │
│ │    publish your own articles on the platform.       │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                              │
│ [        Save Changes        ]                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Profile Page - Reporter Badge

When reporter status is enabled, a badge appears next to the username:

**Private Profile View:**
```
┌─────────────────────────────────────────────────────────────┐
│                    [Profile Picture]                         │
│                                                              │
│              username [🗞️ Reporter]                          │
│              Member since January 2024                       │
│                                                              │
│ Account Information                                          │
│ ─────────────────────────────────────────────────────────── │
│ Username: username                                           │
│ Name: John Doe                                              │
│ Email: user@example.com                                     │
│ Bio: [User bio text...]                                     │
└─────────────────────────────────────────────────────────────┘
```

**Public Profile View:**
```
┌─────────────────────────────────────────────────────────────┐
│                    [Profile Picture]                         │
│                                                              │
│              username [🗞️ Reporter]                          │
│                   John Doe                                   │
│              📅 Member since January 2024                    │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ [User bio text if available...]                             │
└─────────────────────────────────────────────────────────────┘
│                                                              │
│ [Liked Articles] [Authored Articles] [Comments]             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Toggle States

### State 1: Reporter Status Disabled (Default)
```html
☐ I am a reporter/author
ℹ️  Check this to enable article creation and management...
```

**Profile Display:**
- No reporter badge
- No "My Articles" button
- No "Authored Articles" tab on public profile
- Cannot access article management pages

### State 2: Reporter Status Enabled
```html
☑ I am a reporter/author
ℹ️  Check this to enable article creation and management...
```

**Profile Display:**
- Blue reporter badge with newspaper icon
- "My Articles" button visible
- "Authored Articles" tab on public profile
- Full access to article management

## User Flow Diagrams

### Enabling Reporter Status

```
User Profile
     │
     ├─> Click "Edit Profile"
     │
     ├─> Edit Profile Page
     │        │
     │        ├─> Scroll to reporter toggle
     │        │
     │        ├─> Check "I am a reporter/author"
     │        │
     │        └─> Click "Save Changes"
     │
     ├─> Profile Updated
     │        │
     │        ├─> Reporter badge appears
     │        │
     │        ├─> "My Articles" button appears
     │        │
     │        └─> Success message displayed
     │
     └─> Can now create articles
```

### Creating First Article as Reporter

```
Profile Page (with reporter status)
     │
     ├─> Click "My Articles"
     │
     ├─> My Articles Page (empty)
     │        │
     │        └─> Click "Create New Article"
     │
     ├─> Article Creation Form
     │        │
     │        ├─> Fill in title, content, etc.
     │        │
     │        └─> Click "Create Article"
     │
     ├─> Article Created
     │        │
     │        ├─> Redirected to My Articles
     │        │
     │        └─> New article appears in list
     │
     └─> Article visible on public profile
```

## HTML Structure

### Toggle Component
```html
<div class="mb-3">
    <div class="form-check form-switch">
        <input class="form-check-input" 
               type="checkbox" 
               id="is_reporter" 
               name="is_reporter" 
               {% if profile.is_reporter %}checked{% endif %}>
        <label class="form-check-label" for="is_reporter">
            <strong>I am a reporter/author</strong>
        </label>
    </div>
    <div class="form-text">
        <i class="fas fa-info-circle me-1"></i>
        Check this to enable article creation and management. 
        You'll be able to write, edit, and publish your own 
        articles on the platform.
    </div>
</div>
```

### Reporter Badge
```html
<h5 class="mt-3">
    {{ user.username }}
    {% if profile.is_reporter %}
        <span class="badge bg-primary ms-2">
            <i class="fas fa-newspaper me-1"></i>Reporter
        </span>
    {% endif %}
</h5>
```

## CSS Styling

The implementation uses Bootstrap 5 classes:

- **Toggle**: `form-check form-switch` - Modern switch appearance
- **Label**: `form-check-label` - Proper label styling
- **Help Text**: `form-text` - Muted helper text
- **Badge**: `badge bg-primary` - Blue badge with white text
- **Icon**: `fas fa-newspaper` - Font Awesome newspaper icon

## Responsive Behavior

### Desktop (≥992px)
- Toggle appears in full-width form
- Badge displays inline with username
- All text fully visible

### Tablet (768px - 991px)
- Toggle maintains full width
- Badge may wrap on smaller screens
- Help text remains readable

### Mobile (<768px)
- Toggle stacks vertically
- Badge displays below username if needed
- Touch-friendly checkbox size

## Accessibility Features

1. **Semantic HTML**: Proper form structure with labels
2. **Label Association**: `for` attribute links label to input
3. **Help Text**: Descriptive text for screen readers
4. **Keyboard Navigation**: Native checkbox keyboard support
5. **Focus States**: Bootstrap focus styling
6. **ARIA Attributes**: Implicit through proper HTML structure

## Color Scheme

Following the project's design system:

- **Primary Blue**: `bg-primary` for badge and buttons
- **Text Muted**: `text-muted` for help text
- **White Text**: On blue badge for contrast
- **Icon Color**: Inherits from badge background

## Icon Usage

- **Info Icon**: `fas fa-info-circle` - Help text indicator
- **Newspaper Icon**: `fas fa-newspaper` - Reporter badge
- **Check Icon**: Native checkbox checkmark

## Success Messages

After saving profile with reporter toggle:

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ Profile updated successfully.                             │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling

The toggle is a simple boolean field with no validation errors possible:
- Checked = `True`
- Unchecked = `False`
- No invalid states

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- No JavaScript required
- Pure HTML form submission
- Minimal CSS overhead
- Fast page load
- Instant toggle response

## Future UI Enhancements

Potential improvements:
1. **Confirmation Modal**: "Are you sure you want to become a reporter?"
2. **Tooltip**: Hover tooltip with additional info
3. **Animation**: Smooth transition when badge appears
4. **Counter**: Show article count next to badge
5. **Progress Indicator**: Show reporter level/achievements

