# Ollama Integration for News Advance

This document provides comprehensive instructions for setting up and using Ollama with News Advance for advanced AI-powered article analysis.

## What is Ollama?

[Ollama](https://ollama.ai/) is a framework for running large language models (LLMs) locally on your machine. It provides an easy way to download, run, and manage various open-source LLMs without requiring a connection to cloud services.

## Why Ollama?

- **Privacy**: All processing happens locally on your machine
- **No API costs**: No usage fees or API keys required
- **Customization**: Easy to fine-tune models for specific needs
- **Flexibility**: Multiple models available for different tasks
- **Performance**: Fast inference with proper hardware

## Setup Instructions

### 1. Install Ollama

Download and install Ollama from the official website: [https://ollama.ai/download](https://ollama.ai/download)

Ollama is available for:
- Windows
- macOS
- Linux

### 2. Download Recommended Models

After installing Ollama, open a terminal/command prompt and run the following commands to download the recommended models:

```bash
# Download Llama 3 (8B) - Best balance of performance and speed
ollama pull llama3

# Download DeepSeek R1 (8B) - Excellent for complex reasoning tasks
ollama pull deepseek-r1:8b

# Download Mistral (7B) - Alternative model with good performance
ollama pull mistral

# Optional: Download smaller models for faster processing
ollama pull qwen2:1.5b  # Lightweight model for quick tasks
ollama pull phi         # Microsoft's efficient small model
```

### 3. Start the Ollama Service

Ollama typically starts automatically after installation. To manually start it:

- **Windows**: Ollama runs as a service automatically
- **macOS**: Run `ollama serve` in terminal
- **Linux**: Run `ollama serve` in terminal

Verify Ollama is running by visiting `http://localhost:11434` in your browser.

### 4. Configure News Advance

In your `news_advance/settings.py`, ensure the Ollama endpoint is configured:

```python
OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate'
```

You can also set this as an environment variable:

```env
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
```

## Available AI Functions

The following AI-enhanced functions are available in `news_analysis/utils.py`:

### 1. Article Summarization

```python
from news_analysis.utils import summarize_article_with_ai

# Generate a summary of an article
summary = summarize_article_with_ai(article_text, model="llama3")

# Use ML model instead of Ollama
summary = summarize_article_with_ai(article_text, model="ml")

# Force Ollama usage even if ML model is available
summary = summarize_article_with_ai(article_text, model="llama3", use_ml_model=False)
```

### 2. Advanced Sentiment Analysis

```python
from news_analysis.utils import analyze_sentiment_with_ai

# Analyze sentiment with more nuance than VADER
sentiment = analyze_sentiment_with_ai(article_text, model="llama3")
print(sentiment['classification'])  # 'positive', 'negative', or 'neutral'
print(sentiment['score'])           # Score from -1.0 to 1.0
print(sentiment['explanation'])     # Explanation of the sentiment analysis
```

### 3. Political Bias Detection

```python
from news_analysis.utils import detect_political_bias_with_ai

# Detect political bias in an article
bias = detect_political_bias_with_ai(article_text, model="llama3")
print(bias['political_leaning'])    # 'left', 'center-left', 'center', 'center-right', 'right', or 'unknown'
print(bias['bias_score'])           # Score from -1.0 (far left) to 1.0 (far right)
print(bias['confidence'])           # Confidence score from 0.0 to 1.0
print(bias['explanation'])          # Explanation of the bias analysis
```

### 4. Key Insights Extraction

```python
from news_analysis.utils import extract_key_insights_with_ai

# Extract key insights from an article
insights = extract_key_insights_with_ai(article_text, model="llama3", num_insights=5)
for insight in insights:
    print(f"- {insight}")
```

## Using AI Analysis in Management Commands

The `analyze_articles` management command supports AI-enhanced analysis:

```bash
# Use default model (llama3)
python manage.py analyze_articles

# Specify a different model
python manage.py analyze_articles --model deepseek-r1:8b

# Analyze specific articles with AI
python manage.py analyze_articles --article_id 123 --model llama3

# Batch process with AI analysis
python manage.py analyze_articles --limit 50 --model mistral
```

## Recommended Models for Different Tasks

| Task | Primary Model | Alternative | Lightweight Option |
|------|---------------|-------------|-------------------|
| Article Summarization | llama3 | mistral | qwen2:1.5b |
| Sentiment Analysis | llama3 | deepseek-r1:8b | phi |
| Political Bias Detection | deepseek-r1:8b | llama3 | mistral |
| Key Insights Extraction | llama3 | deepseek-r1:8b | mistral |

## Model Performance Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3 | 8B | Medium | High | General analysis, summarization |
| deepseek-r1:8b | 8B | Medium | Very High | Complex reasoning, bias detection |
| mistral | 7B | Fast | High | Quick analysis, general tasks |
| qwen2:1.5b | 1.5B | Very Fast | Medium | Lightweight processing |
| phi | 2.7B | Fast | Medium | Quick sentiment analysis |

## Integration with ML Summarization

News Advance intelligently chooses between ML and Ollama summarization:

1. **ML Model First**: If `USE_ML_SUMMARIZATION=True` and the trained model exists
2. **Ollama Fallback**: If ML model fails or is disabled
3. **Manual Override**: Use `model="ml"` to force ML model usage

```python
# Configuration in settings.py
USE_ML_SUMMARIZATION = True  # Try ML model first
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'

# Force specific behavior
summary = summarize_article_with_ai(text, model="ml")        # Force ML model
summary = summarize_article_with_ai(text, model="llama3")    # Force Ollama
```

## Troubleshooting

### Common Issues

1. **Ollama not running**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama manually
   ollama serve
   ```

2. **Model not found**
   ```bash
   # List installed models
   ollama list
   
   # Pull missing model
   ollama pull llama3
   ```

3. **Connection refused**
   - Ensure Ollama is running on port 11434
   - Check firewall settings
   - Verify `OLLAMA_ENDPOINT` in settings

4. **Slow performance**
   - Use smaller models (qwen2:1.5b, phi)
   - Ensure adequate RAM (8GB+ recommended)
   - Consider GPU acceleration if available

### Checking Ollama Status

```bash
# List all models
ollama list

# Check if Ollama is responding
curl http://localhost:11434/api/tags

# Test a model
ollama run llama3 "Hello, how are you?"
```

### Performance Optimization

1. **Hardware Requirements**
   - **Minimum**: 8GB RAM, CPU-only
   - **Recommended**: 16GB+ RAM, dedicated GPU
   - **Optimal**: 32GB+ RAM, high-end GPU

2. **Model Selection**
   - Use smaller models for development/testing
   - Use larger models for production quality
   - Consider model switching based on task complexity

3. **Text Processing**
   - Longer texts require more processing time
   - The system automatically truncates very long articles
   - Batch processing is more efficient than individual requests

## Advanced Configuration

### Custom Model Parameters

You can modify the Ollama query parameters in `news_analysis/utils.py`:

```python
def query_ollama(prompt, model="llama3", system_prompt=None, max_tokens=1000):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,      # Creativity level (0.0-1.0)
            "top_p": 0.9,           # Nucleus sampling
            "top_k": 40,            # Top-k sampling
        }
    }
```

### Environment Variables

Set these in your environment or `.env` file:

```env
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
OLLAMA_DEFAULT_MODEL=llama3
OLLAMA_TIMEOUT=30
```

## Future Improvements

- **Model Caching**: Implement model result caching for faster repeated analysis
- **Fine-tuning**: Add support for fine-tuning models on news-specific data
- **Batch Processing**: Create management commands for bulk AI analysis
- **Model Comparison**: Add tools to compare results across different models
- **Performance Monitoring**: Track model performance and response times

## API Reference

### Core Functions

#### `query_ollama(prompt, model, system_prompt, max_tokens)`
- **Purpose**: Core function for communicating with Ollama API
- **Returns**: JSON response from Ollama
- **Error Handling**: Returns None on failure, logs errors

#### `summarize_article_with_ai(text, model, use_ml_model)`
- **Purpose**: Generate article summaries using AI
- **Fallback**: ML model → Ollama → None
- **Returns**: Summary string or None

#### `analyze_sentiment_with_ai(text, model)`
- **Purpose**: Advanced sentiment analysis
- **Fallback**: Ollama → VADER sentiment analysis
- **Returns**: Dict with classification, score, explanation

#### `detect_political_bias_with_ai(text, model)`
- **Purpose**: Detect political bias in text
- **Returns**: Dict with political_leaning, bias_score, confidence, explanation

#### `extract_key_insights_with_ai(text, model, num_insights)`
- **Purpose**: Extract key insights from articles
- **Returns**: List of insight strings

For more technical details, see [AI_PROJECT_DOCS.md](AI_PROJECT_DOCS.md).
