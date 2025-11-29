# Google Custom Search API Troubleshooting Guide

This document provides troubleshooting steps for common issues with the Google Custom Search API integration.

## Common Error: 400 Bad Request - Invalid Argument

### Symptoms
```
Google search error: 400 Client Error: Bad Request for url: https://www.googleapis.com/customsearch/v1?...
{
    "error": {
        "code": 400,
        "message": "Request contains an invalid argument.",
        ...
    }
}
```

### Root Causes

#### 1. **Custom Search Engine ID (cx) not configured**
**Problem**: The `WEB_SEARCH_CX` environment variable is empty or not set.

**Solution**: 
- Create a Custom Search Engine at https://programmablesearchengine.google.com/
- Copy the "Search engine ID" 
- Add it to your `.env` file:
  ```
  WEB_SEARCH_CX=your-custom-search-engine-id-here
  ```

#### 2. **Using API Key as Custom Search Engine ID (cx)**
**Problem**: The `WEB_SEARCH_CX` is incorrectly set to the same value as `WEB_SEARCH_API_KEY`.

**Solution**: 
- The API Key and Custom Search Engine ID are **two different values**
- API Key: Obtained from Google Cloud Console (starts with `AIza...`)
- Custom Search Engine ID: Obtained from Programmable Search Engine (random alphanumeric string)
- Ensure your `.env` file has both:
  ```
  WEB_SEARCH_API_KEY=AIzaSy...  # From Google Cloud Console
  WEB_SEARCH_CX=a1b2c3d4e...     # From Programmable Search Engine
  ```

#### 3. **Custom Search API not enabled**
**Problem**: The Custom Search API is not enabled for your Google Cloud project.

**Solution**:
- Visit https://console.cloud.google.com/apis/library
- Search for "Custom Search API"
- Click "Enable"

#### 4. **Invalid query format**
**Problem**: The search query contains invalid characters or is too long.

**Solution**: The code now automatically:
- Trims whitespace
- Truncates queries longer than 1500 characters
- Validates queries before making requests

## Configuration Checklist

Use this checklist to verify your configuration:

- [ ] `.env` file exists in project root
- [ ] `WEB_SEARCH_API_KEY` is set and starts with `AIza`
- [ ] `WEB_SEARCH_CX` is set and is different from the API key
- [ ] Custom Search API is enabled in Google Cloud Console
- [ ] Custom Search Engine is created and configured to search the entire web
- [ ] `ENABLE_WEB_SEARCH=True` in `.env` file
- [ ] Django server has been restarted after changing `.env`

## Verification Steps

### 1. Check Configuration
Run this Python code to verify your settings:

```python
from django.conf import settings

print(f"API Key set: {'Yes' if settings.WEB_SEARCH_API_KEY else 'No'}")
print(f"CX set: {'Yes' if settings.WEB_SEARCH_CX else 'No'}")
print(f"Same value: {'ERROR!' if settings.WEB_SEARCH_API_KEY == settings.WEB_SEARCH_CX else 'OK'}")
print(f"Enable Web Search: {settings.ENABLE_WEB_SEARCH}")
```

### 2. Test Search Functionality
Run this in Django shell (`python manage.py shell`):

```python
from news_analysis.rag_system import WebSearcher

searcher = WebSearcher()
results = searcher.search("test query", num_results=1)
print(f"Results: {len(results)}")
if results:
    print(f"First result: {results[0]['title']}")
```

## Enhanced Error Logging

The updated code now provides detailed error messages:

1. **Configuration validation on initialization**: Warns if API key or CX is missing
2. **Duplicate value detection**: Errors if CX equals API key
3. **Query sanitization**: Validates and logs query issues
4. **Detailed HTTP errors**: Logs the full error response from Google
5. **Separate timeouts**: Distinguishes between timeout and other request errors

## Support Resources

- [Google Custom Search JSON API Documentation](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine Control Panel](https://programmablesearchengine.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)
- Project README: See "Google Custom Search API Setup" section

## Still Having Issues?

If you're still experiencing problems:

1. Check the Django log file (`django.log`) for detailed error messages
2. Verify your Google Cloud project has billing enabled (required for API usage beyond free tier)
3. Check your API quotas in Google Cloud Console
4. Ensure your API key has proper restrictions (or no restrictions for testing)
5. Test your API key and CX directly using curl:

```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CX&q=test"
```

If the curl command fails, the issue is with your Google configuration, not the Django code.
