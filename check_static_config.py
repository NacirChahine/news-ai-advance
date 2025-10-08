#!/usr/bin/env python
"""
Static Files Configuration Checker
Verifies that Django static files are properly configured for development.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_env_file():
    """Check if .env file exists and has correct DJANGO_DEBUG setting"""
    print_header("Checking .env Configuration")
    
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found!")
        print(f"  Create one by copying .env.example:")
        print(f"  cp .env.example .env")
        return False
    
    print_success(".env file exists")
    
    # Read .env file
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Check for DJANGO_DEBUG
    if 'DJANGO_DEBUG=True' in env_content:
        print_success("DJANGO_DEBUG=True is set correctly")
        return True
    elif 'DJANGO_DEBUG=False' in env_content:
        print_error("DJANGO_DEBUG=False (should be True for development)")
        print(f"  Change it to: DJANGO_DEBUG=True")
        return False
    elif 'DEBUG=True' in env_content and 'DJANGO_DEBUG' not in env_content:
        print_warning("Found DEBUG=True but need DJANGO_DEBUG=True")
        print(f"  Change 'DEBUG=True' to 'DJANGO_DEBUG=True'")
        return False
    else:
        print_error("DJANGO_DEBUG not found in .env file")
        print(f"  Add this line: DJANGO_DEBUG=True")
        return False

def check_static_dirs():
    """Check if static directories exist and contain expected files"""
    print_header("Checking Static Files Structure")
    
    base_dir = Path('.')
    static_dir = base_dir / 'static'
    
    if not static_dir.exists():
        print_error("static/ directory not found!")
        return False
    
    print_success("static/ directory exists")
    
    # Check subdirectories
    css_dir = static_dir / 'css'
    js_dir = static_dir / 'js'
    images_dir = static_dir / 'images'
    
    all_good = True
    
    for dir_path, dir_name in [(css_dir, 'css'), (js_dir, 'js'), (images_dir, 'images')]:
        if dir_path.exists():
            print_success(f"static/{dir_name}/ directory exists")
        else:
            print_error(f"static/{dir_name}/ directory not found!")
            all_good = False
    
    # Check for expected files
    expected_files = [
        ('css/site.css', 'Global styles'),
        ('css/article_detail.css', 'Article page styles'),
        ('js/theme.js', 'Theme toggling'),
        ('js/article_actions.js', 'Article save/unsave'),
        ('js/article_detail.js', 'Article page interactions'),
        ('js/article_likes.js', 'Like/dislike functionality'),
        ('js/comments.js', 'Comment system'),
        ('js/preferences.js', 'User preferences'),
        ('images/favicon.ico', 'Site favicon'),
    ]
    
    print("\nChecking expected static files:")
    for file_path, description in expected_files:
        full_path = static_dir / file_path
        if full_path.exists():
            print_success(f"{file_path} - {description}")
        else:
            print_warning(f"{file_path} - {description} (missing)")
            all_good = False
    
    return all_good

def check_settings_py():
    """Check settings.py for correct static files configuration"""
    print_header("Checking settings.py Configuration")
    
    settings_path = Path('news_advance/settings.py')
    if not settings_path.exists():
        print_error("news_advance/settings.py not found!")
        return False
    
    with open(settings_path, 'r') as f:
        settings_content = f.read()
    
    # Check for required settings
    checks = [
        ("STATIC_URL = 'static/'", "STATIC_URL setting"),
        ("STATIC_ROOT", "STATIC_ROOT setting"),
        ("STATICFILES_DIRS", "STATICFILES_DIRS setting"),
        ("django.contrib.staticfiles", "staticfiles app in INSTALLED_APPS"),
    ]
    
    all_good = True
    for check_str, description in checks:
        if check_str in settings_content:
            print_success(description)
        else:
            print_error(f"{description} not found!")
            all_good = False
    
    return all_good

def check_urls_py():
    """Check urls.py for static files URL configuration"""
    print_header("Checking urls.py Configuration")
    
    urls_path = Path('news_advance/urls.py')
    if not urls_path.exists():
        print_error("news_advance/urls.py not found!")
        return False
    
    with open(urls_path, 'r') as f:
        urls_content = f.read()
    
    # Check for required imports and configurations
    checks = [
        ("from django.conf.urls.static import static", "static import"),
        ("from django.contrib.staticfiles.urls import staticfiles_urlpatterns", "staticfiles_urlpatterns import"),
        ("staticfiles_urlpatterns()", "staticfiles_urlpatterns() call"),
    ]
    
    all_good = True
    for check_str, description in checks:
        if check_str in urls_content:
            print_success(description)
        else:
            print_error(f"{description} not found!")
            all_good = False
    
    return all_good

def check_django_debug():
    """Check the actual DEBUG value Django will use"""
    print_header("Checking Django DEBUG Setting")
    
    try:
        # Try to import Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_advance.settings')
        import django
        django.setup()
        from django.conf import settings
        
        if settings.DEBUG:
            print_success(f"Django DEBUG is True (correct for development)")
            return True
        else:
            print_error(f"Django DEBUG is False (should be True for development)")
            print(f"  Check your .env file and ensure DJANGO_DEBUG=True")
            return False
    except Exception as e:
        print_warning(f"Could not check Django settings: {e}")
        return None

def main():
    print(f"\n{BLUE}{'='*60}")
    print(f"  Static Files Configuration Checker")
    print(f"  News Advance Project")
    print(f"{'='*60}{RESET}\n")
    
    results = []
    
    # Run all checks
    results.append(("Environment File", check_env_file()))
    results.append(("Static Directories", check_static_dirs()))
    results.append(("Settings Configuration", check_settings_py()))
    results.append(("URLs Configuration", check_urls_py()))
    
    # Check Django DEBUG (may fail if Django not set up)
    debug_result = check_django_debug()
    if debug_result is not None:
        results.append(("Django DEBUG Value", debug_result))
    
    # Print summary
    print_header("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        if result:
            print_success(f"{check_name}: PASS")
        else:
            print_error(f"{check_name}: FAIL")
    
    print(f"\n{passed}/{total} checks passed\n")
    
    if passed == total:
        print_success("All checks passed! Your static files should work correctly.")
        print(f"\nNext steps:")
        print(f"  1. Restart your Django development server")
        print(f"  2. Clear your browser cache (Ctrl+Shift+Delete)")
        print(f"  3. Visit http://127.0.0.1:8000")
        return 0
    else:
        print_error("Some checks failed. Please fix the issues above.")
        print(f"\nFor detailed help, see: STATIC_FILES_TROUBLESHOOTING.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())

