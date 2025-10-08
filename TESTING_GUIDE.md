# Testing Guide for New Features

This guide provides step-by-step instructions for testing the three new features implemented in News Advance.

---

## Prerequisites

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Create at least two test users for testing privacy and profile features:
   ```bash
   python manage.py createsuperuser
   # Create additional test user through signup page
   ```

3. Ensure you have some news sources and articles in the database:
   ```bash
   python manage.py generate_test_data --sources 5 --articles 20 --users 2
   ```

---

## Feature 1: Public Profile Privacy Setting

### Test Case 1.1: Set Profile to Private
1. Log in as User A
2. Navigate to **Accounts → Preferences**
3. Scroll to **Privacy** section
4. **Uncheck** "Public Profile" toggle
5. Wait for "Preferences saved automatically!" message
6. Log out

### Test Case 1.2: Verify Private Profile (Other User)
1. Log in as User B
2. Navigate to `/accounts/user/userA/` (replace userA with actual username)
3. **Expected**: See "This Profile is Private" message with lock icon
4. **Expected**: No comments, liked articles, or preferred sources visible

### Test Case 1.3: Verify Own Profile Access
1. Log in as User A (profile owner)
2. Navigate to `/accounts/user/userA/`
3. **Expected**: See full profile with all content
4. **Expected**: Privacy setting doesn't affect own view

### Test Case 1.4: Set Profile to Public
1. Log in as User A
2. Navigate to **Accounts → Preferences**
3. **Check** "Public Profile" toggle
4. Wait for success message
5. Log out

### Test Case 1.5: Verify Public Profile
1. Log in as User B
2. Navigate to `/accounts/user/userA/`
3. **Expected**: See full profile with comments, liked articles, and preferred sources tabs

---

## Feature 2: Preferred News Sources

### Test Case 2.1: Add Preferred Source
1. Log in as any user
2. Navigate to **Analysis Tools → Sources Overview** (`/news/sources/`)
3. Click on any source to view its detail page
4. Click **"Add to Preferred"** button (outline-primary with empty star icon)
5. **Expected**: Button changes to **"Remove from Preferred"** (btn-danger with filled star)
6. **Expected**: Success message appears: "[Source Name] added to preferred sources"
7. **Expected**: Message auto-dismisses after 3 seconds

### Test Case 2.2: Remove Preferred Source
1. On the same source detail page
2. Click **"Remove from Preferred"** button (btn-danger)
3. **Expected**: Button changes back to **"Add to Preferred"** (outline-primary)
4. **Expected**: Success message appears: "[Source Name] removed from preferred sources"

### Test Case 2.3: View Preferred Sources in Private Profile
1. Navigate to **Accounts → Your Profile**
2. Scroll to **"Preferred News Sources"** section
3. **Expected**: See list of preferred sources with star icons
4. **Expected**: Each source is clickable and links to source detail page
5. If no preferred sources: **Expected** message "You haven't marked any sources as preferred yet..."

### Test Case 2.4: View Preferred Sources in Public Profile
1. Navigate to your public profile (`/accounts/user/your-username/`)
2. Click on **"Preferred Sources"** tab
3. **Expected**: See list of preferred sources
4. **Expected**: Count in tab label matches number of sources

### Test Case 2.5: Feed Prioritization
1. Mark 2-3 sources as preferred
2. Navigate to **Latest News** (`/news/`)
3. **Expected**: Articles from preferred sources appear at the top of the feed
4. **Expected**: Star icon (⭐) appears next to source name on article cards from preferred sources
5. **Expected**: Tooltip on star says "Preferred Source"

### Test Case 2.6: Non-Authenticated User
1. Log out
2. Navigate to any source detail page
3. **Expected**: No "Add to Preferred" button visible
4. Navigate to `/news/`
5. **Expected**: No star icons on article cards

---

## Feature 3: Profile Pictures & Avatars

### Test Case 3.1: Upload Profile Picture
1. Log in as any user
2. Navigate to **Accounts → Preferences**
3. Scroll to **"Profile Picture"** section
4. **Expected**: See current avatar (letter avatar if no picture uploaded)
5. Click **"Choose File"** and select a valid image (JPG, PNG, or GIF under 2MB)
6. **Expected**: Success message "Profile picture updated successfully!"
7. **Expected**: Preview updates to show uploaded image
8. **Expected**: "Remove Picture" button appears
9. **Expected**: Page reloads after 1.5 seconds

### Test Case 3.2: Invalid File Type
1. Try to upload a PDF or TXT file
2. **Expected**: Error message "Please select a valid image file (JPG, PNG, or GIF)"
3. **Expected**: File input clears

### Test Case 3.3: File Too Large
1. Try to upload an image larger than 2MB
2. **Expected**: Error message "File size must be less than 2MB"
3. **Expected**: File input clears

### Test Case 3.4: Remove Profile Picture
1. With a profile picture uploaded
2. Click **"Remove Picture"** button
3. **Expected**: Confirmation dialog "Are you sure you want to remove your profile picture?"
4. Click OK
5. **Expected**: Success message "Profile picture removed successfully!"
6. **Expected**: Page reloads and shows letter avatar

### Test Case 3.5: Avatar in Comments
1. Navigate to any article detail page
2. Post a comment (or view existing comments)
3. **Expected**: Your avatar appears next to your comment (36x36px circular)
4. If you have a profile picture: **Expected** image displays
5. If no profile picture: **Expected** letter avatar with colored gradient background

### Test Case 3.6: Letter Avatar Colors
1. View comments from multiple users without profile pictures
2. **Expected**: Each user has a different colored gradient background
3. **Expected**: First letter of username appears in white, centered

### Test Case 3.7: Avatar Image Error Handling
1. Upload a profile picture
2. Manually delete the image file from `media/profile_pics/`
3. Navigate to article with your comments
4. **Expected**: Letter avatar displays as fallback (no broken image icon)

---

## Cross-Feature Testing

### Test Case 4.1: Public Profile with All Features
1. Log in as User A
2. Upload a profile picture
3. Mark 2-3 sources as preferred
4. Post some comments on articles
5. Like some articles
6. Ensure public profile is enabled
7. Log out and log in as User B
8. Navigate to User A's public profile
9. **Expected**: See User A's profile picture (not letter avatar)
10. **Expected**: See "Preferred Sources" tab with User A's preferred sources
11. **Expected**: See comments with User A's avatar
12. **Expected**: See liked articles

### Test Case 4.2: Private Profile Hides Everything
1. Log in as User A
2. Set profile to private
3. Log out and log in as User B
4. Navigate to User A's public profile
5. **Expected**: "This Profile is Private" message
6. **Expected**: No tabs visible
7. **Expected**: No preferred sources, comments, or liked articles visible

### Test Case 4.3: Preferred Source Feed with Avatars
1. Log in and mark sources as preferred
2. Navigate to `/news/`
3. **Expected**: Articles from preferred sources at top with star icons
4. Click on an article from a preferred source
5. Post a comment
6. **Expected**: Your avatar appears next to comment
7. **Expected**: Source name has star icon in article header

---

## Accessibility Testing

### Test Case 5.1: Keyboard Navigation
1. Use Tab key to navigate through:
   - Preferred source toggle button
   - Profile picture upload input
   - Privacy toggle
2. **Expected**: All elements are reachable and have visible focus states
3. Press Enter/Space on buttons
4. **Expected**: Actions trigger correctly

### Test Case 5.2: Screen Reader
1. Use a screen reader (NVDA, JAWS, or VoiceOver)
2. Navigate to source detail page
3. **Expected**: Button announces "Add to Preferred Sources" or "Remove from Preferred Sources"
4. Navigate to preferences
5. **Expected**: File input announces "Profile Picture" with format and size requirements
6. Navigate to comments
7. **Expected**: Avatar images have alt text with username

### Test Case 5.3: Contrast Ratios
1. Test in both light and dark themes
2. Use browser DevTools or contrast checker
3. **Expected**: All text has at least 4.5:1 contrast ratio
4. **Expected**: Large text has at least 3:1 contrast ratio
5. **Expected**: Interactive elements have 3:1 contrast ratio

---

## Mobile Testing

### Test Case 6.1: Responsive Design
1. Open site on mobile device or use browser DevTools responsive mode
2. Test all features at 375px, 768px, and 1024px widths
3. **Expected**: All buttons are at least 44x44px (touch target size)
4. **Expected**: Layouts adapt properly
5. **Expected**: No horizontal scrolling

### Test Case 6.2: Touch Interactions
1. On mobile device, tap preferred source button
2. **Expected**: Button responds immediately
3. Tap profile picture upload
4. **Expected**: Native file picker opens
5. Tap privacy toggle
6. **Expected**: Toggle switches smoothly

---

## Browser Compatibility

Test all features in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Performance Testing

### Test Case 7.1: Feed Loading with Preferred Sources
1. Mark 5+ sources as preferred
2. Navigate to `/news/`
3. **Expected**: Page loads in under 2 seconds
4. **Expected**: No visible lag when scrolling

### Test Case 7.2: Profile Picture Upload
1. Upload a 1.9MB image
2. **Expected**: Upload completes in under 5 seconds
3. **Expected**: Preview updates smoothly

### Test Case 7.3: Avatar Loading in Comments
1. Navigate to article with 20+ comments
2. **Expected**: All avatars load without blocking page render
3. **Expected**: Letter avatars display immediately
4. **Expected**: Image avatars load progressively

---

## Edge Cases

### Test Case 8.1: User with No Username
1. Create user with empty username (if possible)
2. **Expected**: Letter avatar shows "?" or first character of email

### Test Case 8.2: Very Long Source Names
1. Create source with 100+ character name
2. Mark as preferred
3. **Expected**: Name truncates properly in profile display
4. **Expected**: Full name visible on hover or in tooltip

### Test Case 8.3: Concurrent Preference Changes
1. Open two browser windows logged in as same user
2. Toggle preferred source in both windows simultaneously
3. **Expected**: Both windows update correctly
4. **Expected**: No duplicate entries in database

---

## Regression Testing

Ensure existing features still work:
- [ ] Article save/unsave functionality
- [ ] Article like/dislike functionality
- [ ] Comment posting and editing
- [ ] Comment voting
- [ ] Theme switching (light/dark)
- [ ] Search functionality
- [ ] Source filtering
- [ ] User authentication (login/logout/signup)

---

## Bug Reporting Template

If you find a bug, report it with:

```
**Feature**: [Preferred Sources / Profile Pictures / Privacy]
**Test Case**: [Test case number and name]
**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:

**Actual Behavior**:

**Browser**: [Chrome 120 / Firefox 121 / etc.]
**Device**: [Desktop / Mobile / Tablet]
**Theme**: [Light / Dark]
**Screenshots**: [Attach if applicable]
```

---

## Success Criteria

All features are considered successfully implemented when:
- ✅ All test cases pass
- ✅ No console errors in browser DevTools
- ✅ WCAG AA accessibility compliance verified
- ✅ Works in all supported browsers
- ✅ Responsive on all screen sizes
- ✅ No performance degradation
- ✅ No regressions in existing features

