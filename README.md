# MovieLens 100K LLM Rating Predictor

This project uses Large Language Models (LLMs) to predict how users will rate movies, replacing traditional collaborative filtering methods. It works by generating natural language prompts based on a user's movie history and demographics, and asking an LLM to predict their rating for a new item.

## Setup Instructions

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup API Keys** (Optional, but recommended):
   The script supports OpenAI and Gemini apis natively out of the box. If no API keys are found, it uses a dummy predictor that returns `3` for testing logic.
   
   To use OpenAI:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-key-here"
   ```

   To use Gemini (Google GenAI):
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-key-here"
   ```

3. **Run the Prediction Pipeline!**
   You can run the full test dataset of 20,000 ratings, but keep in mind that testing the full set would consume significant API credits. 
   
   For a quick test on 10 random samples:
   ```bash
   python evaluate.py --subset 10
   ```
   
   For the full dataset:
   ```bash
   python evaluate.py --subset 0
   ```

## Output
The script will output the evaluated pairs, compute Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE), and write the resulting predictions to `predictions.csv`.
