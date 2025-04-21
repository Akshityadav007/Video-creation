import logging
from pathlib import Path
from datetime import datetime
from typing import List
import subprocess
import moviepy.editor as mpe

from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.createFrames import MAX_WORKERS, split_story, ImageGenerator

logger = logging.getLogger(__name__)

def create_video(script: str, category: str = "cartoon") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create session directories
    video_dir = Path("videos") / timestamp
    audio_dir = Path("audio") / timestamp
    frames_dir = Path("frames") / timestamp
    
    for dir in [video_dir, audio_dir, frames_dir]:
        dir.mkdir(parents=True, exist_ok=True)
    
    chunks = split_story(script)
    logger.info(f"Processing {len(chunks)} story chunks")

    chunk_paths = process_chunks_parallel(chunks, category, video_dir, audio_dir, frames_dir)
    final_path = combine_video_chunks(chunk_paths, video_dir)
    
    logger.info(f"✅ Final video generated: {final_path}")
    return final_path

def process_chunks_parallel(chunks: List[str], category: str, 
                          video_dir: Path, audio_dir: Path, frames_dir: Path) -> List[Path]:
    chunk_paths = [None] * len(chunks)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(
            process_single_chunk, 
            chunk, idx, category, video_dir, audio_dir, frames_dir
        ): idx for idx, chunk in enumerate(chunks)}
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                chunk_paths[idx] = future.result()
            except Exception as e:
                logger.error(f"Chunk {idx} failed: {str(e)}")
                raise
    
    return [p for p in chunk_paths if p is not None]

def process_single_chunk(chunk: str, idx: int, category: str, 
                       video_dir: Path, audio_dir: Path, frames_dir: Path) -> Path:
    # Create per-chunk video directory
    chunk_video_dir = video_dir / f"chunk_{idx:03d}"
    chunk_video_dir.mkdir(exist_ok=True)
    
    # Generate assets in their respective directories
    audio_path = audio_dir / f"chunk_{idx:03d}.mp3"
    image_path = frames_dir / f"chunk_{idx:03d}.png"
    
    # Generate assets
    generate_audio_chunk(chunk, audio_path)
    generate_image_chunk(chunk, category, image_path)
    
    # Create video clip
    chunk_video_path = chunk_video_dir / "clip.mp4"
    create_video_clip(audio_path, image_path, chunk_video_path)
    
    return chunk_video_path

def generate_audio_chunk(text: str, output_path: Path) -> Path:
    from utils.createAudio import generateAudio
    return Path(generateAudio(text, output_path=str(output_path)))

def generate_image_chunk(prompt: str, category: str, output_path: Path) -> Path:
    generator = ImageGenerator(category=category)
    generator.generate_image(prompt, output_path)
    return output_path

def create_video_clip(audio_path: Path, image_path: Path, output_path: Path) -> Path:
    try:
        audio = mpe.AudioFileClip(str(audio_path))
        clip = mpe.ImageClip(str(image_path)).set_duration(audio.duration)
        clip = clip.set_audio(audio)
        
        clip.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None
        )
        return output_path
    finally:
        if 'clip' in locals(): clip.close()
        if 'audio' in locals(): audio.close()

def combine_video_chunks(chunk_paths: List[Path], session_dir: Path) -> Path:
    list_file = session_dir / "chunks.txt"
    with open(list_file, "w") as f:
        for p in chunk_paths:
            f.write(f"file '{str(p.absolute()).replace('\\', '/')}'\n")
    
    final_path = session_dir / "final_video.mp4"
    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-r", "24",  # explicit framerate
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(final_path),
        "-y"
    ], check=True)
    
    return final_path