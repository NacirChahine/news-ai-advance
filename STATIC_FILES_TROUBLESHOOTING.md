# Static Files Troubleshooting Guide

## Quick Fix for Static File Serving Issues

If you're experiencing issues where CSS and JavaScript files are not loading correctly (404 errors or wrong MIME types), follow these steps:

### Step 1: Check Your `.env` File

Open your `.env` file and ensure it contains:

```env
DJANGO_DEBUG=True
```

**Important**: The variable must be named `DJANGO_DEBUG` (not just `DEBUG`). This is required for Django's development server to properly serve static files.

### Step 2: Verify Static Files Exist

Check that your static files are in the correct locations:

```
static/
├── css/
│   ├── site.css
│   └── article_detail.css
├── js/
│   ├── theme.js
│   ├── article_actions.js
│   ├── article_detail.js
│   ├── article_likes.js
│   ├── comments.js
│   └── preferences.js
└── images/
    └── favicon.ico
```

### Step 3: Restart the Development Server

After making changes to `.env`:

1. Stop the Django development server (Ctrl+C)
2. Restart it:
   ```bash
   python manage.py runserver
   ```

### Step 4: Clear Browser Cache

Static file issues can be caused by browser caching:

- **Chrome/Edge**: Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
- **Firefox**: Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
- Or use **Hard Reload**: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

### Step 5: Verify the Fix

1. Open your browser's Developer Tools (F12)
2. Go to the **Console** tab
3. Navigate to `http://127.0.0.1:8000`
4. Check for any remaining errors

You should see no errors related to static files. CSS and JavaScript files should load with correct MIME types:
- CSS files: `text/css`
- JavaScript files: `application/javascript` or `text/javascript`

## Common Error Messages and Solutions

### Error: "Refused to apply style... MIME type ('text/html') is not a supported stylesheet MIME type"

**Cause**: Django is returning a 404 error page (HTML) instead of the CSS file.

**Solution**: 
1. Ensure `DJANGO_DEBUG=True` in `.env`
2. Verify the CSS file exists in `static/css/`
3. Restart the development server

### Error: "Failed to load resource: the server responded with a status of 404"

**Cause**: The static file cannot be found.

**Solution**:
1. Check the file path in your template matches the actual file location
2. Ensure `{% load static %}` is at the top of your template
3. Verify the file exists in the `static/` directory

### Error: "GET /static/css/site.css HTTP/1.1" 404

**Cause**: Static files are not being served by Django.

**Solution**:
1. Check `DJANGO_DEBUG=True` in `.env`
2. Verify `news_advance/urls.py` includes `staticfiles_urlpatterns()`
3. Restart the development server

## Understanding the Configuration

### Why DJANGO_DEBUG=True is Required

In `news_advance/settings.py`, the DEBUG setting is configured as:

```python
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
```

This means:
- If `DJANGO_DEBUG` is not set, DEBUG defaults to `False`
- Only the exact string `"True"` will enable DEBUG mode
- When DEBUG is False, Django's development server won't serve static files

### URL Configuration

The `news_advance/urls.py` file includes:

```python
# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add staticfiles serving for development server
urlpatterns += staticfiles_urlpatterns()
```

This configuration:
1. Serves media files (user uploads) when DEBUG=True
2. Serves static files from STATIC_ROOT when DEBUG=True
3. Uses `staticfiles_urlpatterns()` as a fallback for development

## Production Deployment Notes

**Important**: Never use Django to serve static files in production!

For production deployment:

1. Set `DJANGO_DEBUG=False` in your production `.env`
2. Run `python manage.py collectstatic` to gather all static files into `STATIC_ROOT`
3. Configure your web server (nginx, Apache, etc.) to serve static files directly
4. Example nginx configuration:

```nginx
location /static/ {
    alias /path/to/your/project/staticfiles/;
}

location /media/ {
    alias /path/to/your/project/media/;
}
```

## Additional Resources

- [Django Static Files Documentation](https://docs.djangoproject.com/en/5.0/howto/static-files/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- Project README: See "Configuration" section for environment variables
- AI_PROJECT_DOCS.md: See "Static Files Configuration" section for technical details

## Still Having Issues?

If you've followed all the steps above and still experiencing problems:

1. Check the Django development server console output for error messages
2. Verify your Python virtual environment is activated
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Check file permissions on the `static/` directory
5. Try accessing a static file directly: `http://127.0.0.1:8000/static/css/site.css`

If the direct URL returns a 404, the issue is with Django's static file serving configuration. If it works but the page doesn't load it, check your template syntax.

