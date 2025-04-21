# ✅ Set Hugging Face cache FIRST (before any imports)
import os
from pathlib import Path

from utils.upload import upload_to_youtube

project_dir = Path(__file__).parent.resolve()
custom_cache = project_dir / ".hf_cache"
os.environ["HF_HOME"] = str(custom_cache)
# os.environ["TRANSFORMERS_CACHE"] = str(custom_cache)
os.environ["HF_HUB_CACHE"] = str(custom_cache)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Now import other modules
import logging
from datetime import datetime
from huggingface_hub import scan_cache_dir
from utils.createAudio import generateAudio
from utils.createFrames import generate_all_images
from utils.createScript import generateStory
from utils.createVideo import create_video


def configure_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"storygen_{timestamp}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)




# Updated main function
if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger()  # Get configured logger
    
    # Generate full script
    title, story = generateStory()
    
    # Create final video
    from utils.createVideo import create_video
    video_path = create_video(story, category="cartoon")
    
    logger.info(f"Video created at: {video_path}")  # Use logger instead of logging

    # Add upload
    upload_to_youtube(video_path=video_path, title=title, description=story)
