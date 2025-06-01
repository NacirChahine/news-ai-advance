"""
Django integration for the fine-tuned summarization model
"""
import os
import logging
from django.conf import settings
from .inference import SummarizationModel

# Configure logging
logger = logging.getLogger(__name__)

# Model instance - will be lazily loaded
_model_instance = None

def get_model_instance():
    """
    Get or create the summarization model instance
    
    Returns:
        SummarizationModel: The model instance
    """
    global _model_instance
    
    if _model_instance is None:
        # Check for a trained model in the configured directory
        model_dir = getattr(settings, 'SUMMARIZATION_MODEL_DIR', None)
        
        if model_dir and os.path.exists(model_dir):
            logger.info(f"Loading fine-tuned summarization model from {model_dir}")
            _model_instance = SummarizationModel(model_dir=model_dir)
        else:
            # Fallback to base model
            fallback_model = getattr(settings, 'SUMMARIZATION_BASE_MODEL', 'facebook/bart-base')
            logger.warning(
                f"Trained model not found in {model_dir if model_dir else 'None'}, "
                f"falling back to {fallback_model}"
            )
            _model_instance = SummarizationModel(model_name=fallback_model)
    
    return _model_instance

def summarize_article_with_ml_model(article_text, max_length=150):
    """
    Generate a summary of an article using the fine-tuned model
    
    Args:
        article_text (str): The article text to summarize
        max_length (int): Maximum length of the generated summary
    
    Returns:
        str: The generated summary, or None if there was an error
    """
    if not article_text:
        return None
    
    try:
        # Get the model
        model = get_model_instance()
        
        # Generate summary
        summary = model.summarize(
            article_text,
            max_summary_length=max_length,
            min_length=min(30, max(10, max_length // 3))  # Adaptive min length
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error summarizing article with ML model: {e}")
        return None
