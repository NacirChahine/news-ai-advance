@echo off
echo Training BBC News Summarization Model
echo ===================================

:: Ensure virtual environment is activated (modify as needed)
call python -m pip install -r ../requirements.txt

:: Run the training script
echo.
echo Starting model training...
python train_summarization_model.py --model_name facebook/bart-base --output_dir ./trained_model --num_train_epochs 3 --batch_size 4 --learning_rate 5e-5 --max_input_length 1024 --max_target_length 128

echo.
echo Training complete! The model is saved in the ./trained_model directory
echo You can now use the model in your application
pause
