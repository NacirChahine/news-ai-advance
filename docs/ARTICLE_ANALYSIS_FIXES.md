# Article Analysis Error Fixes - Complete Summary

## Overview
Fixed multiple critical issues in the article analysis system that were causing JSON parsing errors, embedding extraction failures, and fallacy detection problems.

## Issues Fixed

### 1. **Embedding Extraction Failures** ✅
**Error**: `Failed to extract embedding from response. First 200 chars: ...`

**Root Cause**:  
The `EmbeddingGenerator` was using the wrong Ollama endpoint. It was pointing to the text generation endpoint (`/api/generate`) instead of the embeddings endpoint (`/api/embed`).

**Solution**:
- Changed endpoint from `OLLAMA_ENDPOINT` (which is `/api/generate`) to a dedicated `/api/embed` endpoint
- Added new environment variable `OLLAMA_BASE_URL` to construct the correct embedding URL
- Updated API payload to use `input` parameter instead of `prompt` (correct for embeddings API)
- Enhanced response parsing to handle both single `embedding` and batch `embeddings` formats
- Added proper validation for empty responses

**Files Modified**:
- `news_analysis/rag_system.py` - Complete rewrite of `EmbeddingGenerator` class
- `.env.example` - Added `OLLAMA_BASE_URL` configuration

---

### 2. **JSON Parsing Errors**  ✅
**Error**: `Expecting value: line 1 column 1 (char 0)`

**Root Cause**:  
The code was trying to parse empty strings as JSON after aggressive code fence extraction. The extraction logic would sometimes strip all content, leaving an empty string that caused JSON parsing to fail.

**Solution**:
Enhanced JSON extraction in three functions with:
- Empty string checks before and after code fence extraction
- Safer code fence parsing with try-except blocks
- Fallback to plain text extraction when JSON fails
- Truncated explanations in fallbacks (200 chars) to avoid bloat
- Better debug logging with response previews

**Files Modified**:
- `news_analysis/utils.py`:
  - `analyze_sentiment_with_ai()` - Lines 434-469
  - `detect_political_bias_with_ai()` - Lines 507-552
  - `extract_key_insights_with_ai()` - Already fixed in previous session

---

### 3. **Logical Fallacy Name Mismatch** ✅
**Error**: `Unknown fallacy label from AI: 'Strawman' — skipping (add to catalog if desired)`

**Root Cause**:  
The AI was returning fallacy names with slight variations (e.g., "Strawman" vs "Straw Man", "AdHominem" vs "Ad Hominem") that didn't match the catalog entries exactly.

**Solution**:
Added fuzzy matching with three strategies:
1. **Exact case-insensitive match** (`name__iexact`)
2. **Slug match** (using Django's `slugify`)
3. **Fuzzy match** - Remove spaces, hyphens, underscores and compare
   - "Strawman" → "strawman" matches "Straw Man" → "strawman"
   - "AdHominem" → "adhominem" matches "Ad Hominem" → "adhominem"

**Files Modified**:
- `news_analysis/management/commands/analyze_articles.py` - Lines 465-490

---

## Technical Details

### Ollama API Endpoints

**Text Generation** (`/api/generate`):
```json
Request: {
  "model": "llama3",
  "prompt": "Your prompt here",
  "stream": false
}
Response: {
  "response": "Generated text...",
  "done": true
}
```

**Embeddings** (`/api/embed`):
```json
Request: {
  "model": "llama3",
  "input": "Text to embed"
}
Response: {
  "embedding": [0.123, -0.456, ...]
}
// or batch format:
{
  "embeddings": [[0.123, -0.456, ...]]
}
```

### Environment Variables

Update your `.env` file:
```bash
# For text generation (summarization, sentiment, bias, etc.)
OLLAMA_ENDPOINT=http://localhost:11434/api/generate

# For embeddings (RAG system)
OLLAMA_BASE_URL=http://localhost:11434
```

The embedding endpoint is automatically constructed as `${OLLAMA_BASE_URL}/api/embed`.

---

## Testing

Run the analysis command to verify all fixes:

```bash
python manage.py analyze_articles --article_id <ID> --force
```

**Expected Output** (no more errors):
```
Analyzing: Article Title
  Performing AI sentiment analysis with llama3...
  AI sentiment classification: neutral
  Created sentiment analysis (score: 0.00)
  Performing AI bias analysis with llama3...
  AI bias detection: center (confidence: 0.85)
  Created bias analysis (leaning: center, score: 0.00)
  Detecting logical fallacies with llama3...
  Fuzzy matched 'Strawman' to catalog entry 'Straw Man'
  Created 2 logical fallacy detection(s)
  ...
```

**What You Won't See Anymore**:
- ❌ `Failed to extract embedding from response`
- ❌ `Expecting value: line 1 column 1 (char 0)`
- ❌ `Unknown fallacy label from AI: 'Strawman'`
- ❌ `Extra data: line 2 column 1`

---

## Summary of All Changes

| File | Changes | Lines |
|------|---------|-------|
| `news_analysis/rag_system.py` | Complete rewrite of `EmbeddingGenerator` | 11-103 |
| `news_analysis/utils.py` | Fixed `analyze_sentiment_with_ai` JSON parsing | 434-469 |
| `news_analysis/utils.py` | Fixed `detect_political_bias_with_ai` JSON parsing | 507-552 |
| `news_analysis/utils.py` | Fixed `query_ollama` NDJSON handling | 209-293 |
| `news_analysis/utils.py` | Fixed `extract_key_insights_with_ai` JSON parsing | 492-591 |
| `news_analysis/management/commands/analyze_articles.py` | Added fuzzy fallacy name matching | 465-490 |
| `.env.example` | Added `OLLAMA_BASE_URL` variable | 16-19 |

---

## Migration Guide

If you have an existing `.env` file, add this line:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

No database migrations or other changes needed. The fixes are backward compatible.

---

## Related Documentation

- Previous fixes: `docs/JSON_PARSING_FIXES.md` (NDJSON handling)
- RAG system: `news_analysis/rag_system.py`
- Analysis utilities: `news_analysis/utils.py`
