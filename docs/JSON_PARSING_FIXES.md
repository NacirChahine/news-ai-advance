# JSON Parsing Fixes for RAG System

## Overview
Fixed JSON parsing errors that were occurring during embeddings generation and insights extraction in the RAG (Retrieval-Augmented Generation) system.

## Issues Fixed

### 1. Embeddings Generation Error (rag_system.py)
**Error**: `Extra data: line 2 column 1 (char 92-96)`

**Root Cause**: Ollama's API sometimes returns NDJSON (newline-delimited JSON) format even when `stream=False` is set. This means multiple JSON objects on separate lines instead of a single JSON object.

**Solution**:
- Enhanced `EmbeddingGenerator.generate()` to handle both single JSON and NDJSON responses
- Try parsing as single JSON first
- If that fails, parse each line separately and extract the embedding from the last valid response
- Added proper timeout (30 seconds)
- Improved error logging with response previews

### 2. Insights Extraction Error (utils.py)
**Error**: `Expecting value: line 1 column 1 (char 0)`

**Root Cause**: The JSON extraction logic was too aggressive and sometimes stripped all content, leaving an empty string. Additionally, some LLM responses don't include JSON at all.

**Solution**:
- Improved code fence extraction logic with proper error handling
- Added empty string checks after each extraction step
- Enhanced fallback to plain text extraction when JSON parsing fails
- Added cleaning of list markers and filtering of short lines
- Better logging with response previews for debugging

### 3. Core query_ollama Function (utils.py)
**Root Issue**: The `query_ollama` function wasn't handling NDJSON responses, which caused all downstream functions to fail.

**Solution**:
- Added NDJSON parsing support
- When single JSON parse fails, parse each line separately
- Aggregate the "response" field from all chunks
- Keep the final chunk's metadata (done, model, etc.)
- Added 60-second timeout
- Improved error categorization (timeout vs request error vs general)

## Technical Details

### NDJSON Format
Ollama sometimes uses NDJSON (Newline-Delimited JSON) format where:
- Each line is a complete JSON object
- For streaming responses, each chunk contains a partial "response" field
- The complete response is built by concatenating all "response" fields
- The last chunk contains metadata like "done": true

Example NDJSON response:
```json
{"model":"llama3","created_at":"...","response":"The ","done":false}
{"model":"llama3","created_at":"...","response":"sky ","done":false}
{"model":"llama3","created_at":"...","response":"is blue.","done":true}
```

Final aggregated response: "The sky is blue."

### Fallback Strategy
All JSON parsing now follows this pattern:
1. Try single JSON parse
2. If fail, try NDJSON multiline parse
3. If still fail, extract from plain text with heuristics
4. Log detailed errors for debugging

## Files Modified

1. **news_analysis/rag_system.py**:
   - `EmbeddingGenerator.generate()` - Lines 18-73

2. **news_analysis/utils.py**:
   - `query_ollama()` - Lines 209-293
   - `extract_key_insights_with_ai()` - Lines 492-591

## Testing

After these fixes, the following should work without JSON errors:

1. **Embeddings Generation**:
   ```python
   from news_analysis.rag_system import EmbeddingGenerator
   gen = EmbeddingGenerator()
   embedding = gen.generate("Test text")
   print(f"Generated embedding with {len(embedding)} dimensions")
   ```

2. **Insights Extraction**:
   ```python
   from news_analysis.utils import extract_key_insights_with_ai
   insights = extract_key_insights_with_ai("Article text here...")
   print(f"Extracted {len(insights)} insights")
   ```

3. **Fact-Checking with RAG**:
   ```bash
   python manage.py analyze_articles --article_id <ID> --force
   ```

## Error Logging Improvements

All functions now provide better debugging information:
- Response previews (first 200-300 characters)
- Specific error types (timeout, request, parsing)
- NDJSON chunk counts
- Fallback strategy outcomes

## Notes

- Despite JSON parsing errors, the system often still extracted data successfully (e.g., "saves 3 cleaned insights")
- This is because the fallback plain text extraction was working
- The fixes eliminate the errors entirely and make parsing more robust
- All changes are backward compatible with both old and new Ollama versions
