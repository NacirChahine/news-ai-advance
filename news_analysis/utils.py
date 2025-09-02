"""
Utility functions for news analysis.
"""
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import re
from django.conf import settings
import logging
import requests
import json
import os

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


# Ollama Integration

def query_ollama(prompt, model="llama3", system_prompt=None, max_tokens=1000):
    """
    Send a query to the Ollama API.

    Args:
        prompt (str): The prompt to send to the model
        model (str): The model to use (default: "llama3")
        system_prompt (str): Optional system prompt to guide the model's behavior
        max_tokens (int): Maximum number of tokens to generate

    Returns:
        dict: The response from the Ollama API, or None if there was an error
    """
    # Default Ollama endpoint (assumes Ollama is running locally)
    ollama_endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")

    # Prepare the request payload
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens
        }
    }

    # Add system prompt if provided
    if system_prompt:
        payload["system"] = system_prompt

    try:
        # Make the API request
        response = requests.post(ollama_endpoint, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse and return the response
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Ollama API: {e}")
        return None


def summarize_article_with_ml_model(article_text, max_length=150):
    """
    Generate a summary of an article using the fine-tuned ML model
    This is a wrapper around the ML model integration.

    Args:
        article_text (str): The article text to summarize
        max_length (int): Maximum length of the generated summary

    Returns:
        str: The generated summary, or None if there was an error
    """
    try:
        # Import here to avoid circular imports
        from news_analysis.ml_models.summarization.django_integration import summarize_article_with_ml_model as ml_summarize
        return ml_summarize(article_text, max_length=max_length)
    except ImportError as e:
        logger.error(f"Error importing ML summarization model: {e}")
        return None
    except Exception as e:
        logger.error(f"Error using ML summarization model: {e}")
        return None

# Check if ML summarization is available
try:
    from news_analysis.ml_models.summarization.django_integration import get_model_instance
    # Test if we can load the model (this won't actually load it yet due to lazy loading)
    get_model_instance
    ml_summarization_available = True
    logger.info("ML-based summarization model is available")
except ImportError:
    ml_summarization_available = False
    logger.warning("ML-based summarization model is not available")

def summarize_article_with_ai(article_text, model="llama3", use_ml_model=None, alert_context: str | None = None):
    """
    Generate a concise summary of an article using either:
    1. The fine-tuned ML summarization model (if available and selected)
    2. Ollama LLM API (as fallback or if explicitly selected)

    Args:
        article_text (str): The article text to summarize
        model (str): The model to use - either an Ollama model name or "ml" for the fine-tuned model
        use_ml_model (bool): If True, use ML model; if False, use Ollama; if None, use settings default
        alert_context (str): Optional context to include about related misinformation alerts

    Returns:
        str: The generated summary, or None if there was an error
    """
    if not article_text:
        return None

    # Check if model is explicitly set to "ml"
    if model == "ml":
        use_ml_model = True

    # Determine if we should use the ML model
    if use_ml_model is None:
        # Check settings, default to True if ML model is available
        use_ml_model = getattr(settings, "USE_ML_SUMMARIZATION", ml_summarization_available)

    # Use the ML model if specified and available
    if use_ml_model and ml_summarization_available:
        logger.info("Summarizing article using fine-tuned ML model")
        return summarize_article_with_ml_model(article_text)

    # Otherwise fall back to Ollama
    logger.info(f"Summarizing article using Ollama model: {model}")

    # Truncate very long articles to avoid token limits
    max_chars = 10000
    truncated_text = article_text[:max_chars] + ("..." if len(article_text) > max_chars else "")

    # Create a prompt for summarization
    context_block = f"\n\nKnown related misinformation alerts:\n{alert_context}\n" if alert_context else ""
    prompt = f"""Please provide a concise summary of the following article:{context_block}

{truncated_text}

Summary:"""

    system_prompt = "You are a professional news editor. Create a clear, objective, and concise summary that captures the main points of the article."

    # Query the Ollama API
    response = query_ollama(prompt, model=model, system_prompt=system_prompt, max_tokens=500)

    if response and "response" in response:
        # Remove thinking tags if present
        response_text = response["response"].strip()
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
        return response_text
    return None


def analyze_sentiment_with_ai(text, model="llama3"):
    """
    Analyze the sentiment of a text using Ollama.
    This provides more nuanced sentiment analysis than the VADER-based approach.

    Args:
        text (str): The text to analyze
        model (str): The Ollama model to use

    Returns:
        dict: Dictionary containing sentiment scores and analysis
    """
    if not text:
        return {
            'classification': 'neutral',
            'score': 0,
            'explanation': 'No text provided'
        }

    # Truncate very long texts
    max_chars = 8000
    truncated_text = text[:max_chars] + ("..." if len(text) > max_chars else "")

    # Create a prompt for sentiment analysis
    prompt = f"""Analyze the sentiment of the following text. Determine if it's positive, negative, or neutral,
and provide a score from -1.0 (very negative) to 1.0 (very positive), with 0 being neutral.
Also provide a brief explanation of your analysis.

Text: {truncated_text}

Format your response as JSON with the following structure:
{{
  "classification": "positive/negative/neutral",
  "score": float between -1.0 and 1.0,
  "explanation": "brief explanation"
}}"""

    system_prompt = "You are a sentiment analysis expert. Provide objective analysis of the emotional tone of the text."

    # Query the Ollama API
    response = query_ollama(prompt, model=model, system_prompt=system_prompt)

    if response and "response" in response:
        try:
            # Extract the JSON part from the response
            json_str = response["response"].strip()
            # Handle potential text before or after the JSON
            json_str = json_str.split("```json")[1].split("```")[0] if "```json" in json_str else json_str
            json_str = json_str.split("```")[1].split("```")[0] if "```" in json_str else json_str

            # Parse the JSON
            result = json.loads(json_str)
            return result
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Error parsing sentiment analysis response: {e}")
            # Fallback to basic classification
            response_text = response["response"].lower()
            if "positive" in response_text:
                return {"classification": "positive", "score": 0.5, "explanation": response_text}
            elif "negative" in response_text:
                return {"classification": "negative", "score": -0.5, "explanation": response_text}
            else:
                return {"classification": "neutral", "score": 0, "explanation": response_text}

    # Fallback to VADER if Ollama fails
    vader_result = analyze_sentiment(text)
    return {
        'classification': vader_result['classification'],
        'score': vader_result['compound'],
        'explanation': 'Fallback to VADER sentiment analysis'
    }


def detect_political_bias_with_ai(text, model="llama3"):
    """
    Detect political bias in a text using Ollama.

    Args:
        text (str): The text to analyze
        model (str): The Ollama model to use

    Returns:
        dict: Dictionary containing bias analysis
    """
    if not text:
        return {
            'political_leaning': 'unknown',
            'bias_score': 0,
            'confidence': 0,
            'explanation': 'No text provided'
        }

    # Truncate very long texts
    max_chars = 8000
    truncated_text = text[:max_chars] + ("..." if len(text) > max_chars else "")

    # Create a prompt for bias detection
    prompt = f"""Analyze the political bias of the following text. Determine where it falls on the political spectrum:
left, center-left, center, center-right, or right. Provide a bias score from -1.0 (far left) to 1.0 (far right),
with 0 being perfectly neutral. Also provide a confidence score from 0.0 to 1.0 and a brief explanation.

Text: {truncated_text}

Format your response as JSON with the following structure:
{{
  "political_leaning": "left/center-left/center/center-right/right/unknown",
  "bias_score": float between -1.0 and 1.0,
  "confidence": float between 0.0 and 1.0,
  "explanation": "brief explanation"
}}"""

    system_prompt = "You are a political analyst with expertise in media bias. Provide an objective analysis of political bias in the text."

    # Query the Ollama API
    response = query_ollama(prompt, model=model, system_prompt=system_prompt)

    if response and "response" in response:
        try:
            # Extract the JSON part from the response
            json_str = response["response"].strip()
            # Handle potential text before or after the JSON
            json_str = json_str.split("```json")[1].split("```")[0] if "```json" in json_str else json_str
            json_str = json_str.split("```")[1].split("```")[0] if "```" in json_str else json_str

            # Parse the JSON
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Error parsing bias detection response: {e}")
            # Fallback to basic classification
            response_text = response["response"].lower()
            if "left" in response_text:
                return {"political_leaning": "left", "bias_score": -0.5, "confidence": 0.3, "explanation": response_text}
            elif "right" in response_text:
                return {"political_leaning": "right", "bias_score": 0.5, "confidence": 0.3, "explanation": response_text}
            else:
                return {"political_leaning": "center", "bias_score": 0, "confidence": 0.3, "explanation": response_text}

    return {
        'political_leaning': 'unknown',
        'bias_score': 0,
        'confidence': 0,
        'explanation': 'Failed to analyze bias'
    }


def extract_key_insights_with_ai(text, model="llama3", num_insights=5):
    """
    Extract key insights from an article using Ollama.

    Args:
        text (str): The article text to analyze
        model (str): The Ollama model to use
        num_insights (int): Number of insights to extract

    Returns:
        list: List of key insights extracted from the text
    """
    if not text:
        return []

    # Truncate very long texts
    max_chars = 8000
    truncated_text = text[:max_chars] + ("..." if len(text) > max_chars else "")

    # Create a prompt for extracting insights
    prompt = f"""Extract the {num_insights} most important insights from the following article:

{truncated_text}

Format your response as a JSON array of strings, each representing a key insight:
[
  "First key insight",
  "Second key insight",
  ...
]"""

    system_prompt = "You are a research analyst. Identify the most important and substantive insights from the text."

    # Query the Ollama API
    response = query_ollama(prompt, model=model, system_prompt=system_prompt)

    if response and "response" in response:
        try:
            # Extract the JSON part from the response
            json_str = response["response"].strip()
            # Handle potential text before or after the JSON
            json_str = json_str.split("```json")[1].split("```")[0] if "```json" in json_str else json_str
            json_str = json_str.split("```")[1].split("```")[0] if "```" in json_str else json_str

            # Parse the JSON
            insights = json.loads(json_str)
            return insights if isinstance(insights, list) else []
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Error parsing insights extraction response: {e}")
            # Try to extract insights from plain text response
            lines = response["response"].strip().split("\n")
            insights = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
            return insights[:num_insights] if insights else []

    return []


# --- Fact-checking helpers ---

def extract_claims(text: str, max_claims: int = 5) -> list[str]:
    """Extract likely fact-checkable claims from text.
    Uses spaCy when available; falls back to NLTK sentence tokenization.
    Heuristics prefer sentences with named entities, numbers, quotes, or report verbs.
    """
    if not text:
        return []

    sentences = []
    try:
        if nlp:
            doc = nlp(text[:100000])
            sentences = [s.text.strip() for s in doc.sents]
        else:
            sentences = nltk.sent_tokenize(text)
    except Exception:
        sentences = nltk.sent_tokenize(text)

    def score_sentence(sent: str) -> float:
        s = sent.strip()
        if len(s) < 40 or len(s) > 300:
            return -1
        score = 0.0
        # Numbers, dates, percentages
        if re.search(r"[0-9]|%|\$", s):
            score += 1.5
        # Quotes
        if '"' in s or "'" in s:
            score += 0.4
        # Reporting verbs
        if re.search(r"\b(said|reported|stated|according to|announced|estimated|claims?)\b", s, re.I):
            score += 0.8
        # Named entities via spaCy
        if nlp:
            try:
                ents = nlp(s).ents
                if any(ent.label_ in {"PERSON", "ORG", "GPE", "DATE", "PERCENT", "MONEY", "TIME", "NORP"} for ent in ents):
                    score += 1.2
            except Exception:
                pass
        # Declarative ending
        if s.endswith('.'):
            score += 0.2
        return score

    # Deduplicate near-identical sentences
    seen = set()
    unique_sents = []
    for s in sentences:
        key = re.sub(r"\s+", " ", s.lower())[:180]
        if key not in seen:
            seen.add(key)
            unique_sents.append(s)

    scored = [(score_sentence(s), s) for s in unique_sents]
    # keep only positive scores
    scored = [t for t in scored if t[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_claims]]


def verify_claim_with_ai(claim: str, context_text: str | None = None, model: str = "llama3") -> dict:
    """Verify a claim using an LLM via Ollama.
    Returns dict with: rating, confidence (0..1), explanation, sources (str or list)
    """
    if not claim:
        return {"rating": "unverified", "confidence": 0.0, "explanation": "Empty claim", "sources": []}

    # Truncate context to avoid token bloat
    ctx = (context_text or "")
    max_chars = 6000
    ctx = ctx[:max_chars] + ("..." if len(ctx) > max_chars else "")

    rating_choices = [
        "true", "mostly_true", "half_true", "mostly_false", "false", "pants_on_fire", "unverified"
    ]

    prompt = (
        "Fact-check the following claim. Use the context if helpful, but do not assume the claim is true unless you can justify it with general knowledge or reliable sources.\n\n"
        f"Claim:\n{claim}\n\n"
        f"Context:\n{ctx}\n\n"
        "Respond ONLY as strict JSON with this schema:\n"
        "{\n"
        "  \"rating\": \"one of: true, mostly_true, half_true, mostly_false, false, pants_on_fire, unverified\",\n"
        "  \"confidence\": 0.0-1.0,\n"
        "  \"explanation\": \"concise explanation\",\n"
        "  \"sources\": [\"optional URL or citation strings\"]\n"
        "}\n"
    )

    system_prompt = (
        "You are a professional fact-checker. Be accurate and conservative. "
        "If insufficient information, return rating 'unverified'. Prefer citing 1-3 reputable sources."
    )

    resp = query_ollama(prompt, model=model, system_prompt=system_prompt, max_tokens=700)
    if resp and "response" in resp:
        raw = resp["response"].strip()
        # Strip possible code fences
        if "```" in raw:
            try:
                raw = raw.split("```json")[1].split("```")[0]
            except Exception:
                try:
                    raw = raw.split("```", 1)[1].split("```", 1)[0]
                except Exception:
                    raw = raw
        try:
            data = json.loads(raw)
            rating = str(data.get("rating", "unverified")).lower().strip()
            if rating not in rating_choices:
                rating = "unverified"
            confidence = data.get("confidence")
            try:
                confidence = float(confidence)
                if confidence < 0 or confidence > 1:
                    confidence = None
            except Exception:
                confidence = None
            explanation = str(data.get("explanation", "")).strip()
            sources = data.get("sources", [])
            if isinstance(sources, list):
                src_str = "; ".join([str(s) for s in sources if str(s).strip()])
            else:
                src_str = str(sources)
            return {
                "rating": rating,
                "confidence": confidence if confidence is not None else 0.5,
                "explanation": explanation or "AI verification result",
                "sources": src_str[:1000]
            }
        except Exception as e:
            logger.error(f"Error parsing fact-check response: {e}")
            # Heuristic fallback
            low = raw.lower()
            rating = "unverified"
            if "pants on fire" in low:
                rating = "pants_on_fire"
            elif "mostly false" in low:
                rating = "mostly_false"
            elif "half true" in low or "partly true" in low:
                rating = "half_true"
            elif "mostly true" in low:
                rating = "mostly_true"
            elif "true" in low:
                rating = "true"
            elif "false" in low:
                rating = "false"
            return {
                "rating": rating,
                "confidence": 0.4,
                "explanation": raw[:500],
                "sources": ""
            }

    # Total failure fallback
    return {"rating": "unverified", "confidence": 0.0, "explanation": "Verification failed", "sources": ""}
