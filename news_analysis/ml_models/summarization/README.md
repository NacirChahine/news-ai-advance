# News Article Summarization Model

This module provides a fine-tuned transformer model for summarizing news articles, trained on the BBC News Summary dataset.

## Overview

The summarization model uses a pre-trained transformer (default: BART) fine-tuned on the [BBC News Summary dataset](https://huggingface.co/datasets/gopalkalpande/bbc-news-summary) to generate concise, accurate summaries of news articles.

## Setup and Installation

1. Install required dependencies:
   ```
   pip install -r ../requirements.txt
   ```

2. Train the model (this may take several hours depending on your hardware):
   ```
   # On Windows
   train_model.bat

   # On Linux/Mac
   python train_summarization_model.py --model_name facebook/bart-base --output_dir ./trained_model
   ```

3. The trained model will be saved to the `./trained_model` directory.

## Usage

The model is automatically integrated with the NewsAdvance application. When the application needs to summarize an article, it will:

1. Try to use the fine-tuned model first (if available)
2. Fall back to Ollama if the fine-tuned model is not available

You can control this behavior through the Django settings:

```python
# In settings.py
USE_ML_SUMMARIZATION = True  # Set to False to always use Ollama
SUMMARIZATION_MODEL_DIR = '/path/to/trained_model'
```

## Manual Testing

To test the model outside of the Django application:

```python
from news_analysis.ml_models.summarization.inference import SummarizationModel

# Initialize the model
model = SummarizationModel(model_dir='./trained_model')

# Generate a summary
article_text = "Your long article text here..."
summary = model.summarize(article_text)
print(summary)
```

You can also use the command line interface:

```
python inference.py --model_dir ./trained_model --input_file article.txt --output_file summary.txt
```

## Training Details

The model is trained with the following default parameters:

- Base model: facebook/bart-base
- Max input length: 1024 tokens
- Max summary length: 128 tokens
- Training epochs: 3
- Batch size: 4
- Learning rate: 5e-5

You can adjust these parameters in the training script for better results.

## Performance

The model is evaluated using ROUGE metrics, which measure the overlap between the generated summaries and the reference summaries in the dataset.

Typical performance metrics after training:
- ROUGE-1: ~40-45%
- ROUGE-2: ~20-25%
- ROUGE-L: ~35-40%

## Integration with Existing System

The model automatically integrates with the existing `summarize_article_with_ai` function in `news_analysis/utils.py`, providing a seamless transition between Ollama and the ML model.
