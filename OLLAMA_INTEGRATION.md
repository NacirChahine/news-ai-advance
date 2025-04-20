# Ollama Integration for News Advance

This document provides instructions for setting up and using Ollama with News Advance for advanced AI-powered article analysis.

## What is Ollama?

[Ollama](https://ollama.ai/) is a framework for running large language models (LLMs) locally on your machine. It provides an easy way to download, run, and manage various open-source LLMs without requiring a connection to cloud services.

## Why Ollama?

- **Privacy**: All processing happens locally on your machine
- **No API costs**: No usage fees or API keys required
- **Customization**: Easy to fine-tune models for specific needs
- **Flexibility**: Multiple models available for different tasks

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
# Download Llama 3 (8B) - Good balance of performance and speed
ollama pull llama3

# Download DeepSeek R1 (8B) - Best performance for complex tasks
# ollama run deepseek-r1:8b

# Optional: Download Mistral (7B) - Alternative model with good performance
ollama pull mistral

# Optional: Download Phi-2 (2.7B) - Smaller, faster model for less complex tasks
ollama pull phi
```

### 3. Start the Ollama Service

Ollama should start automatically after installation. If it's not running, you can start it manually:

- **Windows**: Run Ollama from the Start menu
- **macOS**: Run Ollama from Applications
- **Linux**: Run `ollama serve` in a terminal

The Ollama API will be available at `http://localhost:11434` by default.

### 4. Environment Configuration (Optional)

If you need to use a different Ollama endpoint (e.g., running on a different machine or port), you can set the `OLLAMA_ENDPOINT` environment variable:

```bash
# For Windows (PowerShell)
$env:OLLAMA_ENDPOINT = "http://your-server:11434/api/generate"

# For Linux/macOS
export OLLAMA_ENDPOINT="http://your-server:11434/api/generate"
```

Alternatively, add this to your `.env` file:

```
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
```

## Using the AI Functions

The following functions are available in `news_analysis/utils.py`:

### Article Summarization

```python
from news_analysis.utils import summarize_article_with_ai

# Generate a summary of an article
summary = summarize_article_with_ai(article_text, model="llama3")
```

### Advanced Sentiment Analysis

```python
from news_analysis.utils import analyze_sentiment_with_ai

# Analyze sentiment with more nuance than VADER
sentiment = analyze_sentiment_with_ai(article_text, model="llama3")
print(sentiment['classification'])  # 'positive', 'negative', or 'neutral'
print(sentiment['score'])           # Score from -1.0 to 1.0
print(sentiment['explanation'])     # Explanation of the sentiment analysis
```

### Political Bias Detection

```python
from news_analysis.utils import detect_political_bias_with_ai

# Detect political bias in an article
bias = detect_political_bias_with_ai(article_text, model="llama3")
print(bias['political_leaning'])    # 'left', 'center-left', 'center', 'center-right', 'right', or 'unknown'
print(bias['bias_score'])           # Score from -1.0 (far left) to 1.0 (far right)
print(bias['confidence'])           # Confidence score from 0.0 to 1.0
print(bias['explanation'])          # Explanation of the bias analysis
```

### Key Insights Extraction

```python
from news_analysis.utils import extract_key_insights_with_ai

# Extract key insights from an article
insights = extract_key_insights_with_ai(article_text, model="llama3", num_insights=5)
for insight in insights:
    print(f"- {insight}")
```

## Recommended Models for Different Tasks

| Task | Recommended Model | Alternative |
|------|------------------|-------------|
| Article Summarization | llama3 | mistral |
| Sentiment Analysis | llama3 | phi |
| Political Bias Detection | llama3 | mistral |
| Key Insights Extraction | llama3 | mistral |

## Troubleshooting

### Common Issues

1. **Ollama not running**: Ensure the Ollama service is running by visiting `http://localhost:11434` in your browser.

2. **Model not found**: If you get a "model not found" error, make sure you've downloaded the model with `ollama pull <model_name>`.

3. **Slow responses**: LLMs can be resource-intensive. Consider:
   - Using a smaller model like `phi` for faster responses
   - Reducing the input text length
   - Upgrading your hardware (especially GPU)

4. **Out of memory**: If you encounter memory issues:
   - Close other applications
   - Use a smaller model
   - Reduce the `max_tokens` parameter in the `query_ollama` function

### Checking Ollama Status

To check which models are installed and their status:

```bash
ollama list
```

To check if Ollama is running properly:

```bash
curl http://localhost:11434/api/tags
```

## Performance Considerations

- **Hardware Requirements**: LLMs perform best with a dedicated GPU, but can run on CPU-only systems (with slower performance)
- **Text Length**: Longer texts require more processing time and memory
- **Model Size**: Larger models (like llama3) provide better quality but require more resources than smaller models (like phi)

## Future Improvements

- Implement model caching for faster repeated analysis
- Add support for fine-tuning models on news-specific data
- Create a management command to batch process articles with AI analysis