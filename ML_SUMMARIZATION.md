# ML-Powered News Summarization

This document provides comprehensive information about the custom-trained BART summarization model built specifically for News Advance, trained on the BBC News Summary dataset.

## Overview

News Advance includes a fine-tuned transformer model for generating high-quality summaries of news articles. The model is based on Facebook's BART (Bidirectional and Auto-Regressive Transformers) architecture and has been specifically trained on the BBC News Summary dataset to understand news writing patterns and generate professional-quality summaries.

## Model Architecture

### Base Model
- **Architecture**: BART (Bidirectional and Auto-Regressive Transformers)
- **Base Model**: `facebook/bart-base`
- **Model Type**: Sequence-to-sequence transformer
- **Parameters**: ~140M parameters

### Training Configuration
- **Dataset**: [BBC News Summary](https://huggingface.co/datasets/gopalkalpande/bbc-news-summary)
- **Max Input Length**: 1024 tokens
- **Max Summary Length**: 128 tokens
- **Training Epochs**: 3 (default)
- **Batch Size**: 4 (default)
- **Learning Rate**: 5e-5
- **Optimizer**: AdamW

### Generation Parameters
- **Beam Search**: 4 beams
- **Min Length**: 30 tokens (adaptive)
- **No Repeat N-gram**: 3
- **Early Stopping**: Enabled

## Performance Metrics

The model has been evaluated using standard summarization metrics:

| Metric | Score | Description |
|--------|-------|-------------|
| ROUGE-1 | ~40-45% | Unigram overlap between generated and reference summaries |
| ROUGE-2 | ~20-25% | Bigram overlap between generated and reference summaries |
| ROUGE-L | ~35-40% | Longest common subsequence between summaries |

These scores indicate strong performance comparable to other news summarization models.

## Installation and Setup

### Prerequisites

```bash
# Install required dependencies
cd news_analysis/ml_models
pip install -r requirements.txt
```

Required packages:
- `transformers>=4.40.0`
- `torch>=1.9.0`
- `datasets>=2.0.0`
- `evaluate>=0.4.0`
- `nltk>=3.8`
- `numpy>=1.21.0`

### Training the Model

#### Option 1: Using the Batch Script (Windows)

```bash
cd news_analysis/ml_models/summarization
train_model.bat
```

#### Option 2: Direct Python Execution

```bash
cd news_analysis/ml_models/summarization
python train_summarization_model.py --model_name facebook/bart-base --output_dir ./trained_model
```

#### Training Parameters

You can customize the training process with these parameters:

```bash
python train_summarization_model.py \
    --model_name facebook/bart-base \
    --output_dir ./trained_model \
    --max_input_length 1024 \
    --max_target_length 128 \
    --batch_size 4 \
    --num_train_epochs 3 \
    --learning_rate 5e-5 \
    --warmup_steps 500 \
    --weight_decay 0.01 \
    --logging_steps 100 \
    --eval_steps 500 \
    --save_steps 1000
```

### Training Process

1. **Dataset Loading**: Downloads and preprocesses the BBC News Summary dataset
2. **Tokenization**: Converts text to tokens using BART tokenizer
3. **Model Initialization**: Loads the pre-trained BART model
4. **Training Loop**: Fine-tunes the model on news summarization task
5. **Evaluation**: Computes ROUGE metrics on validation set
6. **Model Saving**: Saves the trained model and tokenizer

Expected training time:
- **CPU Only**: 4-8 hours
- **GPU (RTX 3080)**: 1-2 hours
- **GPU (RTX 4090)**: 30-60 minutes

## Usage

### Automatic Integration

The model is automatically integrated with News Advance and will be used when available:

```python
from news_analysis.utils import summarize_article_with_ai

# Automatically uses ML model if available, falls back to Ollama
summary = summarize_article_with_ai(article_text)

# Force ML model usage
summary = summarize_article_with_ai(article_text, model="ml")
```

### Direct Model Usage

You can also use the model directly:

```python
from news_analysis.ml_models.summarization.inference import SummarizationModel

# Initialize the model
model = SummarizationModel(model_dir='./trained_model')

# Generate a summary
article_text = "Your long article text here..."
summary = model.summarize(
    article_text,
    max_summary_length=150,
    min_length=30,
    num_beams=4
)
print(summary)
```

### Command Line Interface

```bash
cd news_analysis/ml_models/summarization

# Summarize text directly
python inference.py --model_dir ./trained_model --text "Your article text here"

# Summarize from file
python inference.py --model_dir ./trained_model --input_file article.txt --output_file summary.txt
```

### Django Integration

The model integrates seamlessly with Django through the `django_integration.py` module:

```python
from news_analysis.ml_models.summarization.django_integration import summarize_article_with_ml_model

# Generate summary with Django integration
summary = summarize_article_with_ml_model(article_text, max_length=150)
```

## Configuration

### Django Settings

Configure the model behavior in `news_advance/settings.py`:

```python
# ML Models Configuration
SUMMARIZATION_MODEL_DIR = BASE_DIR / 'news_analysis' / 'ml_models' / 'summarization' / 'trained_model'
SUMMARIZATION_BASE_MODEL = 'facebook/bart-base'  # Fallback if trained model not available
USE_ML_SUMMARIZATION = True  # Set to False to always use Ollama instead
```

### Model Parameters

You can adjust generation parameters:

```python
# In your code
summary = model.summarize(
    text,
    max_input_length=1024,      # Maximum input tokens
    max_summary_length=128,     # Maximum summary tokens
    min_length=30,              # Minimum summary tokens
    num_beams=4,                # Beam search width
    no_repeat_ngram_size=3      # Prevent repetition
)
```

## File Structure

```
news_analysis/ml_models/summarization/
├── README.md                           # Model documentation
├── requirements.txt                    # Python dependencies
├── train_model.bat                     # Windows training script
├── train_summarization_model.py        # Training script
├── inference.py                        # Inference utilities
├── django_integration.py               # Django integration
└── trained_model/                      # Trained model directory
    ├── config.json                     # Model configuration
    ├── generation_config.json          # Generation parameters
    ├── pytorch_model.bin               # Model weights
    ├── tokenizer_config.json           # Tokenizer configuration
    ├── tokenizer.json                  # Tokenizer data
    ├── vocab.json                      # Vocabulary
    ├── merges.txt                      # BPE merges
    └── special_tokens_map.json         # Special tokens
```

## Model Comparison

### ML Model vs Ollama

| Aspect | ML Model (BART) | Ollama (LLM) |
|--------|-----------------|--------------|
| **Quality** | High (news-specific) | Very High (general) |
| **Speed** | Fast | Medium |
| **Consistency** | Very High | High |
| **Resource Usage** | Low-Medium | Medium-High |
| **Offline Capability** | Yes | Yes |
| **Customization** | High | Medium |

### When to Use Each

**Use ML Model When:**
- You need consistent, fast summarization
- Processing large volumes of articles
- Working with limited computational resources
- Requiring news-specific summarization style

**Use Ollama When:**
- You need more creative or detailed summaries
- Processing diverse content types
- Requiring explanatory or analytical summaries
- Working with complex or technical articles

## Troubleshooting

### Common Issues

1. **Model Not Found**
   ```
   Error: Model directory not found
   ```
   **Solution**: Train the model first or check the path in settings

2. **CUDA Out of Memory**
   ```
   RuntimeError: CUDA out of memory
   ```
   **Solution**: Reduce batch size or use CPU-only mode

3. **Slow Training**
   **Solution**: Use GPU acceleration or reduce dataset size

4. **Poor Summary Quality**
   **Solution**: Increase training epochs or adjust generation parameters

### Performance Optimization

1. **GPU Acceleration**
   ```python
   # Ensure CUDA is available
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   ```

2. **Memory Management**
   ```python
   # Use gradient checkpointing for large models
   model.gradient_checkpointing_enable()
   ```

3. **Batch Processing**
   ```python
   # Process multiple articles at once
   summaries = model.batch_summarize(article_list)
   ```

## Advanced Features

### Custom Training Data

To train on your own dataset:

```python
# Modify the training script to use custom data
dataset = load_dataset("path/to/your/dataset")
```

### Fine-tuning Existing Model

```python
# Continue training from existing checkpoint
python train_summarization_model.py \
    --model_name ./trained_model \
    --output_dir ./fine_tuned_model \
    --num_train_epochs 1
```

### Model Evaluation

```python
# Evaluate model performance
from evaluate import load
rouge = load("rouge")

# Compute ROUGE scores
results = rouge.compute(
    predictions=generated_summaries,
    references=reference_summaries
)
```

## Integration with Analysis Pipeline

The ML summarization model is integrated into the article analysis pipeline:

1. **Article Processing**: New articles are processed through `analyze_articles` command
2. **Summary Generation**: ML model generates summaries automatically
3. **Fallback Handling**: Falls back to Ollama if ML model fails
4. **Storage**: Summaries are stored in the `NewsArticle.summary` field

```python
# In analyze_articles management command
def generate_summary(self, article):
    summary = summarize_article_with_ai(article.content, model="ml")
    if summary:
        article.summary = summary
        article.is_summarized = True
        article.save()
```

## Future Enhancements

1. **Multi-language Support**: Train models for different languages
2. **Domain Adaptation**: Fine-tune for specific news domains (sports, politics, etc.)
3. **Length Control**: Better control over summary length
4. **Style Transfer**: Generate summaries in different styles
5. **Real-time Training**: Continuous learning from new articles

## Contributing

To contribute to the ML summarization module:

1. Fork the repository
2. Create a feature branch
3. Make your changes to the model or training code
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## References

- [BART Paper](https://arxiv.org/abs/1910.13461)
- [BBC News Summary Dataset](https://huggingface.co/datasets/gopalkalpande/bbc-news-summary)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [ROUGE Metrics](https://en.wikipedia.org/wiki/ROUGE_(metric))

For more technical details about the overall system architecture, see [AI_PROJECT_DOCS.md](AI_PROJECT_DOCS.md).