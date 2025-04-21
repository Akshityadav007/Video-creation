import os
from pathlib import Path
import random
from dotenv import load_dotenv
import google.generativeai as genai  # Correct import
from datetime import datetime
import logging
import warnings
import re

import pandas as pd

# Load environment variables
load_dotenv()

# Set your API keys via environment variable
gemini_api_key = os.getenv("GEMINI_API_KEY")

def getScript() -> str:
    df = pd.read_csv("prompts/jungle_story_prompts.csv")

    row_number = random.randint(1, 98)
    topic = df.iloc[row_number - 1, 0]
    prompt = (
        f"Write a concise children's story of maximum upto 300 characters about: {topic}."
        " Do not add any special characters in it, text and ! are acceptable only."
    )

    return prompt

def check_text_length(text: str, max_len: int = 300) -> str:
    cleaned = re.sub(r'\s+', ' ', text).strip()
    cleaned = cleaned.replace("\n\n", "\n")
    if len(cleaned) > 500:
        raise
    elif len(cleaned) > max_len:
        warnings.warn(f"Text length ({len(cleaned)}) exceeds {max_len} chars", UserWarning)
    return text

def generateStory() -> str:
    prompt = getScript()
    try:
        logging.info(f"Generating story for prompt: {prompt[63:113]}...")
        
        # Configure Gemini client
        genai.configure(api_key=gemini_api_key)
        
        # Initialize model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        
        story = check_text_length(response.text)
        logging.info(f"Generated story length: {len(story)} characters")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outputDir = Path(f"story/{timestamp}")
        outputDir.mkdir(parents=True, exist_ok=True)

        storyPath = outputDir / "story.txt"
        with open(storyPath, "w") as f:
            f.write(story)
        logging.info(f"Story saved to: {storyPath}")

        return prompt[63:113], story
    
    except Exception as e:
        logging.error(f"Story generation failed: {str(e)}")
        raise