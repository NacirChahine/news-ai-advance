"""
Utility functions for news analysis.
"""
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import re
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Ensure NLTK data is available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt')

# Load spaCy model if available, or provide a warning
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model 'en_core_web_sm' not found. Some analysis features may not work.")
    logger.warning("Install with: python -m spacy download en_core_web_sm")
    nlp = None


def analyze_sentiment(text):
    """
    Analyze the sentiment of a text using VADER.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing sentiment scores and classification
    """
    if not text:
        return {
            'compound': 0,
            'pos': 0,
            'neg': 0,
            'neu': 1.0,
            'classification': 'neutral'
        }
    
    # Initialize the sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    # Get the sentiment scores
    scores = sia.polarity_scores(text)
    
    # Add a text classification based on the compound score
    if scores['compound'] >= 0.05:
        scores['classification'] = 'positive'
    elif scores['compound'] <= -0.05:
        scores['classification'] = 'negative'
    else:
        scores['classification'] = 'neutral'
    
    return scores


def extract_named_entities(text, entity_types=None):
    """
    Extract named entities from text using spaCy.
    
    Args:
        text (str): The text to analyze
        entity_types (list): List of entity types to include (e.g., ['PERSON', 'ORG'])
                            If None, all entities are returned
    
    Returns:
        list: List of dictionaries containing entity text, type, and start/end positions
    """
    if not text or not nlp:
        return []
    
    # Process the text with spaCy
    doc = nlp(text[:100000])  # Limit text length for performance
    
    # Extract entities
    entities = []
    for ent in doc.ents:
        if entity_types is None or ent.label_ in entity_types:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    
    return entities


def extract_main_topics(text, top_n=5):
    """
    Extract main topics from text using frequency analysis.
    This is a simple implementation - in production, more sophisticated
    approaches like LDA or transformer-based topic modeling would be used.
    
    Args:
        text (str): The text to analyze
        top_n (int): Number of top topics to return
        
    Returns:
        list: List of topic strings
    """
    if not text or not nlp:
        return []
    
    # Process the text with spaCy
    doc = nlp(text[:100000])  # Limit text length for performance
    
    # Count noun phrases
    noun_phrases = {}
    for chunk in doc.noun_chunks:
        # Clean and normalize the noun phrase
        phrase = re.sub(r'[^\w\s]', '', chunk.text.lower()).strip()
        if len(phrase) > 3 and not any(c.is_stop for c in chunk):
            if phrase in noun_phrases:
                noun_phrases[phrase] += 1
            else:
                noun_phrases[phrase] = 1
    
    # Get the top phrases by frequency
    top_phrases = sorted(noun_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [phrase for phrase, _ in top_phrases]


def calculate_readability_score(text):
    """
    Calculate readability metrics for a text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing readability metrics
    """
    if not text:
        return {
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'avg_sentence_length': 0,
            'avg_word_length': 0
        }
    
    # Tokenize text into sentences and words
    sentences = nltk.sent_tokenize(text)
    words = nltk.word_tokenize(text)
    
    # Filter out punctuation
    words = [word for word in words if any(c.isalpha() for c in word)]
    
    if not words or not sentences:
        return {
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'avg_sentence_length': 0,
            'avg_word_length': 0
        }
    
    # Count syllables (simple approximation)
    def count_syllables(word):
        word = word.lower()
        # Count vowel groups as syllables
        syllables = len(re.findall(r'[aeiouy]+', word))
        # Special cases
        if word.endswith('e'):
            syllables -= 1
        if word.endswith('le'):
            syllables += 1
        if syllables == 0:
            syllables = 1
        return syllables
    
    syllable_count = sum(count_syllables(word) for word in words)
    
    # Calculate metrics
    word_count = len(words)
    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count
    avg_word_length = sum(len(word) for word in words) / word_count
    
    # Flesch Reading Ease
    flesch_reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (syllable_count / word_count))
    
    # Flesch-Kincaid Grade Level
    flesch_kincaid_grade = 0.39 * avg_sentence_length + 11.8 * (syllable_count / word_count) - 15.59
    
    return {
        'flesch_reading_ease': round(flesch_reading_ease, 2),
        'flesch_kincaid_grade': round(flesch_kincaid_grade, 2),
        'avg_sentence_length': round(avg_sentence_length, 2),
        'avg_word_length': round(avg_word_length, 2)
    }
