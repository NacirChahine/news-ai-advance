# Quick Fix Guide - Static Files Not Loading

## The Problem
Your CSS and JavaScript files are not loading because Django's DEBUG mode is disabled.

## The Solution (3 Simple Steps)

### Step 1: Update Your `.env` File

Open the `.env` file in your project root and find the line with `DEBUG` or `DJANGO_DEBUG`.

**Change it to:**
```env
DJANGO_DEBUG=True
```

**Important**: It must be `DJANGO_DEBUG=True` (not just `DEBUG=True`)

### Step 2: Restart Django Server

In your terminal where Django is running:
1. Press `Ctrl+C` to stop the server
2. Run: `python manage.py runserver`

### Step 3: Clear Browser Cache

In your browser:
- Press `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac) for a hard reload

## Verify It's Fixed

1. Open your browser to `http://127.0.0.1:8000`
2. Press `F12` to open Developer Tools
3. Go to the **Console** tab
4. You should see **no errors** about CSS or JavaScript files

## Still Not Working?

Run the configuration checker:
```bash
python check_static_config.py
```

This will tell you exactly what's wrong and how to fix it.

## Need More Help?

See the detailed guides:
- `STATIC_FILES_FIX_SUMMARY.md` - Complete explanation of the fix
- `STATIC_FILES_TROUBLESHOOTING.md` - Detailed troubleshooting steps

