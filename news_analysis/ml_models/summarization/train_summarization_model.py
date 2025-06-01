"""
Train a text summarization model on the BBC News Summary dataset
"""
import os
import argparse
import logging
import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
)
from datasets import load_dataset, load_metric
import nltk
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Train a summarization model")
    parser.add_argument(
        "--model_name", 
        type=str, 
        default="facebook/bart-base", 
        help="Name of the pretrained model to fine-tune"
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="./trained_model", 
        help="Directory to save the model"
    )
    parser.add_argument(
        "--max_input_length", 
        type=int, 
        default=1024, 
        help="Maximum length of input sequences"
    )
    parser.add_argument(
        "--max_target_length", 
        type=int, 
        default=128, 
        help="Maximum length of target sequences"
    )
    parser.add_argument(
        "--batch_size", 
        type=int, 
        default=4, 
        help="Batch size for training and evaluation"
    )
    parser.add_argument(
        "--learning_rate", 
        type=float, 
        default=5e-5, 
        help="Learning rate"
    )
    parser.add_argument(
        "--num_train_epochs", 
        type=int, 
        default=3, 
        help="Number of training epochs"
    )
    parser.add_argument(
        "--save_steps", 
        type=int, 
        default=500, 
        help="Save checkpoint every X steps"
    )
    parser.add_argument(
        "--eval_steps", 
        type=int, 
        default=500, 
        help="Evaluate every X steps"
    )
    parser.add_argument(
        "--gradient_accumulation_steps", 
        type=int, 
        default=2, 
        help="Number of updates steps to accumulate before backward pass"
    )
    return parser.parse_args()

def download_nltk_dependencies():
    """Download the NLTK data needed for the ROUGE metric"""
    try:
        nltk.data.find("punkt")
    except (LookupError, OSError):
        nltk.download("punkt", quiet=True)

def preprocess_function(examples, tokenizer, max_input_length, max_target_length):
    """Preprocess the dataset for training"""
    # Combine document and summary fields based on dataset structure
    inputs = examples["document"]
    targets = examples["summary"]
    
    # Tokenize inputs
    model_inputs = tokenizer(
        inputs, 
        max_length=max_input_length, 
        padding="max_length", 
        truncation=True
    )
    
    # Tokenize targets
    labels = tokenizer(
        targets, 
        max_length=max_target_length, 
        padding="max_length", 
        truncation=True
    )
    
    # Replace padding token id with -100 so they're ignored in the loss
    labels["input_ids"] = [
        [(l if l != tokenizer.pad_token_id else -100) for l in label] 
        for label in labels["input_ids"]
    ]
    
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

def compute_metrics(eval_pred, tokenizer, metric):
    """Compute ROUGE metrics for evaluation"""
    predictions, labels = eval_pred
    # Decode predictions
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    
    # Replace -100 in the labels (which is the default padding label) with tokenizer.pad_token_id
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # ROUGE expects a newline after each sentence
    decoded_preds = ["\n".join(nltk.sent_tokenize(pred.strip())) for pred in decoded_preds]
    decoded_labels = ["\n".join(nltk.sent_tokenize(label.strip())) for label in decoded_labels]
    
    # Compute ROUGE scores
    result = metric.compute(
        predictions=decoded_preds, 
        references=decoded_labels, 
        use_stemmer=True
    )
    
    # Extract ROUGE scores
    result = {key: value.mid.fmeasure * 100 for key, value in result.items()}
    
    # Add mean generated length
    prediction_lens = [len(pred.split()) for pred in decoded_preds]
    result["gen_len"] = np.mean(prediction_lens)
    
    return {k: round(v, 4) for k, v in result.items()}

def main():
    """Main function to train the summarization model"""
    args = parse_args()
    
    # Download NLTK data
    download_nltk_dependencies()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Log info about the training
    logger.info(f"Training with the following parameters: {args}")
    
    # Load the BBC News Summary dataset
    logger.info("Loading dataset")
    dataset = load_dataset("gopalkalpande/bbc-news-summary")
    
    # Load tokenizer and model
    logger.info(f"Loading tokenizer and model: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name)
    
    # Ensure tokenizer has a padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Preprocess the dataset
    logger.info("Preprocessing the dataset")
    tokenized_datasets = dataset.map(
        lambda examples: preprocess_function(
            examples, tokenizer, args.max_input_length, args.max_target_length
        ),
        batched=True,
        remove_columns=dataset["train"].column_names,
    )
    
    # Load ROUGE metric
    logger.info("Loading ROUGE metric")
    metric = load_metric("rouge")
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding="max_length",
        max_length=args.max_input_length
    )
    
    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        evaluation_strategy="steps",
        eval_steps=args.eval_steps,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        weight_decay=0.01,
        save_total_limit=3,
        num_train_epochs=args.num_train_epochs,
        predict_with_generate=True,
        fp16=torch.cuda.is_available(),
        save_steps=args.save_steps,
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="rouge2",
        push_to_hub=False,
    )
    
    # Initialize trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda eval_pred: compute_metrics(eval_pred, tokenizer, metric),
    )
    
    # Train the model
    logger.info("Starting training")
    trainer.train()
    
    # Save the model and tokenizer
    logger.info(f"Saving model to {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    logger.info("Training completed!")

if __name__ == "__main__":
    main()
