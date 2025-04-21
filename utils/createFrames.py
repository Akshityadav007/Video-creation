from functools import wraps
import math
import os
from pathlib import Path
from datetime import datetime
import random
import re
import time
import torch
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

# Configuration
MAX_FRAMES = 4
MAX_SENTENCES_PER_CHUNK = 1
MAX_WORKERS = 1
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
LOWMEM_WIDTH = 384
LOWMEM_HEIGHT = 384

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RELIABLE_MODELS = {
    "cartoon": {
        "Lykon/DreamShaper",
        "artificialguybr/storybookredmond-1-5-version-storybook-kids-lora-style-for-sd-1-5",
        "prompthero/openjourney-v4",
        "ainz/diseny-pixar",
        "nitrosocke/mo-di-diffusion",
        "ProGamerGov/Min-Illust-Background-Diffusion",
        "dreamlike-art/dreamlike-photoreal-2.0"
    },
    "motivational": {
        "stabilityai/stable-diffusion-xl-base-1.0",
        "HyperX-Sentience/MJ-LoRA-Midjourney-SD-Mix",
        "Shakker-Labs/FLUX.1-dev-ControlNet-Union-Pro-2.0",
    },
    "anime": {
        "cagliostrolab/animagine-xl-3.0"
    }
}


def retry(max_attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator


def split_story(story: str):
    sentences = re.split(r'(?<=[.!?])\s+', story.strip())
    total = len(sentences)
    if total == 0:
        return []
    chunk_size = math.ceil(total / MAX_FRAMES)
    chunks = [' '.join(sentences[i: i + chunk_size]) for i in range(0, total, chunk_size)]
    return chunks


def generate_all_images(story_text: str, imageType: str, output_dir: Path = Path("frames")):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)

    chunks = split_story(story_text)[:MAX_FRAMES]
    logger.info(f"Processing {len(chunks)} story chunks (max {MAX_FRAMES})")

    generator = ImageGenerator(category=imageType)
    futures, image_paths = [], []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for idx, chunk in enumerate(chunks, 1):
            out = session_dir / f"frame_{idx:03d}.png"
            image_paths.append(out)
            futures.append(executor.submit(generator.generate_image, chunk, out))

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                logger.error(f"Generation failed: {e}")

    logger.info(f"All images saved in: {session_dir}")
    return sorted(image_paths), session_dir


class ImageGenerator:
    _shared_pipe = None

    def __init__(self, model_id=None, category="cartoon"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.category = category
        self.model_id = model_id or self._get_working_model()
        self.pipe = None
        self._lock = threading.Lock()

        if ImageGenerator._shared_pipe is None:
            self.load_model()
            ImageGenerator._shared_pipe = self.pipe
        else:
            self.pipe = ImageGenerator._shared_pipe

    def _validate_cache_files(self, model_id):
        required_files = ["model_index.json"]
        cache_path = Path(os.getenv("HF_HOME")) / f"models--{model_id.replace('/', '--')}"
        if not cache_path.exists():
            return False
        snapshot_dirs = list((cache_path / "snapshots").glob("*"))
        if not snapshot_dirs:
            return False
        snapshot_dir = snapshot_dirs[0]
        return all((snapshot_dir / f).exists() for f in required_files)

    def load_model(self):
        with self._lock:
            if self.pipe is not None:
                return

            logger.info(f"Loading model: {self.model_id}")
            use_fp16 = self.device == "cuda"
            variant = "fp16" if use_fp16 else None
            is_cached = self.model_id in self._get_cached_models()

            try:
                if "xl" in self.model_id.lower():
                    self.pipe = StableDiffusionXLPipeline.from_pretrained(
                        self.model_id,
                        torch_dtype=torch.float16 if use_fp16 else torch.float32,
                        use_safetensors=True,
                        variant=variant,
                        local_files_only=is_cached
                    )
                else:
                    self.pipe = StableDiffusionPipeline.from_pretrained(
                        self.model_id,
                        torch_dtype=torch.float16 if use_fp16 else torch.float32,
                        use_safetensors=True,
                        variant=variant,
                        local_files_only=is_cached
                    )
            except Exception as e:
                logger.warning(f"Model load failed: {str(e)}")
                raise

            self.pipe = self.pipe.to(self.device)

    def _get_cached_models(self):
        cache_path = Path(os.getenv("HF_HOME"))
        cached_models = []
        if cache_path.exists():
            for model_dir in cache_path.glob("models--*"):
                model_name = model_dir.name.replace("models--", "").replace("--", "/")
                if model_name in RELIABLE_MODELS[self.category]:
                    cached_models.append(model_name)
        return list(set(cached_models))

    def _clean_bad_cache(self, model_id):
        cache_path = Path(os.getenv("HF_HOME"))
        model_dir = cache_path / f"models--{model_id.replace('/', '--')}"
        if model_dir.exists():
            import shutil
            shutil.rmtree(model_dir)

    @retry(max_attempts=3, delay=5)
    def _try_download_model(self, model):
        if "xl" in model.lower():
            return StableDiffusionXLPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16,
                local_files_only=False
            )
        else:
            return StableDiffusionPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16,
                local_files_only=False
            )

    def generate_image(self, prompt: str, output_path: Path):
        """
        Generates an image based on the provided prompt and saves it to the specified output path.
        """
        if self.pipe is None:
            self.load_model()

        logger.info(f"Generating image for prompt: {prompt}")
        final_prompt = f"Whimsical 8K cartoon of {prompt}, vibrant colors, bold outlines, cute and playful style, kid-friendly, magical background, high contrast, soft rounded shapes, fantasy elements"
        image = self.pipe(final_prompt).images[0]
        image.save(output_path)
        logger.info(f"Image saved to: {output_path}")

    def _get_working_model(self):
        if self.category not in RELIABLE_MODELS:
            logger.warning(f"Invalid category '{self.category}'. Defaulting to 'cartoon'")
            self.category = "cartoon"
        models = RELIABLE_MODELS[self.category]

        cached_models = [
            m for m in self._get_cached_models()
            if m in models and self._validate_cache_files(m)
        ]

        if cached_models:
            logger.info(f"Using cached models: {cached_models}")
            for model in cached_models:
                try:
                    StableDiffusionPipeline.from_pretrained(
                        model,
                        local_files_only=True,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                    )
                    return model
                except Exception as e:
                    self._clean_bad_cache(model)

        for model in models:
            try:
                self._try_download_model(model)
                return model
            except Exception:
                continue

        raise RuntimeError("No valid model found.")
