"""
Inference script for using the fine-tuned summarization model
"""
import os
import torch
import logging
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class SummarizationModel:
    """Class for handling text summarization with a fine-tuned model"""
    
    def __init__(self, model_dir=None, model_name="facebook/bart-base"):
        """
        Initialize the summarization model
        
        Args:
            model_dir (str): Path to the directory containing the fine-tuned model
            model_name (str): Name of the pretrained model if model_dir is not provided
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model and tokenizer
        if model_dir and os.path.exists(model_dir):
            logger.info(f"Loading fine-tuned model from {model_dir}")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        else:
            logger.info(f"Loading base model {model_name}")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Ensure tokenizer has padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def summarize(self, text, max_input_length=1024, max_summary_length=128, 
                  num_beams=4, min_length=30, no_repeat_ngram_size=3):
        """
        Generate a summary for the given text
        
        Args:
            text (str): The text to summarize
            max_input_length (int): Maximum length of input text
            max_summary_length (int): Maximum length of generated summary
            num_beams (int): Number of beams for beam search
            min_length (int): Minimum length of the summary
            no_repeat_ngram_size (int): Size of n-grams that cannot be repeated
            
        Returns:
            str: The generated summary
        """
        if not text:
            logger.warning("Empty text provided for summarization")
            return ""
        
        # Truncate very long texts if needed
        truncated_text = text[:100000]  # Limit for very long texts
        
        # Tokenize the input
        inputs = self.tokenizer(
            truncated_text, 
            max_length=max_input_length, 
            truncation=True, 
            padding="max_length", 
            return_tensors="pt"
        ).to(self.device)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_length=max_summary_length,
                min_length=min_length,
                num_beams=num_beams,
                no_repeat_ngram_size=no_repeat_ngram_size,
                early_stopping=True
            )
        
        # Decode summary
        summary = self.tokenizer.decode(
            summary_ids[0], 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=True
        )
        
        return summary

# For direct usage from command line
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a summary using a fine-tuned model")
    parser.add_argument("--model_dir", type=str, help="Directory containing the fine-tuned model")
    parser.add_argument("--text", type=str, help="Text to summarize")
    parser.add_argument("--input_file", type=str, help="Input file containing text to summarize")
    parser.add_argument("--output_file", type=str, help="Output file to write the summary")
    args = parser.parse_args()
    
    # Initialize the model
    model = SummarizationModel(model_dir=args.model_dir)
    
    # Get the input text
    if args.text:
        text = args.text
    elif args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError("Either --text or --input_file must be provided")
    
    # Generate summary
    summary = model.summarize(text)
    
    # Output summary
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(summary)
    else:
        print("\nSummary:")
        print(summary)
