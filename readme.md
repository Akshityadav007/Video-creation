Required to download: 
```console
winget install ImageMagick.Q16-HDRI
```

- There are multiple models(listed in models.txt) which can be used to generate frames.
- The first you run a model it will take sometime.

```markdown
# Automated Video Creation Tool 🎥

A Python-based automated video creation system that generates videos using images from Pexels, text-to-speech narration, and exports final videos with subtitles. Includes YouTube upload capability.

## Features ✨

- 📷 Fetch random images from Pexels based on keywords
- 🎙 Convert text to speech using Google Text-to-Speech
- 📹 Create video compositions with MoviePy
- 📝 Add animated subtitles to videos
- 📤 Upload videos directly to YouTube
- ⚙️ Configurable settings through JSON file

## Installation 📦

1. Clone the repository:
```bash
git clone https://github.com/Akshityadav007/Video-creation.git
cd Video-creation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration ⚙️

1. Get API keys:
   - [Pexels API Key](https://www.pexels.com/api/new/)
   - [Google Cloud Credentials](https://console.cloud.google.com/apis/credentials)

2. Rename `config.json.example` to `config.json` and update:
```json
{
  "pexels_api_key": "YOUR_PEXELS_API_KEY",
  "youtube_credentials": "client_secret.json",
  "max_images": 5,
  "video_resolution": [1920, 1080]
}
```

3. Enable YouTube API and download OAuth 2.0 credentials from Google Cloud Console

## Usage 🚀

Basic command:
```bash
python video_creation.py --text "Your script text here" --keywords "keyword1,keyword2"
```

Arguments:
- `--text`: Text content for video narration (required)
- `--keywords`: Comma-separated keywords for image search (required)
- `--mode`: Operation mode (`create`, `upload`, or `both`) [default: both]
- `--output`: Output filename [default: output.mp4]

Example:
```bash
python video_creation.py \
  --text "Exploring the beauty of nature through different seasons" \
  --keywords "forest,river,mountains" \
  --mode both \
  --output nature_video.mp4
```

## Project Structure 📂

```
├── video_creation.py          # Main script
├── utils/
│   ├── download_content.py    # Image download utilities
│   ├── generate_audio.py      # Text-to-speech generation
│   ├── video_maker.py         # Video composition logic
│   └── upload_youtube.py      # YouTube upload functions
├── config.json.example        # Configuration template
├── requirements.txt           # Dependency list
└── notes.txt                  # Development notes
```

## Dependencies 📦

- MoviePy
- Requests
- Google API Client
- python-dotenv
- gTTS

## Contributing 🤝

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer ⚠️

Ensure you have proper rights to all content used. This tool is intended for legitimate use with properly licensed assets.

---

**Note:** Replace placeholder values in `config.json` with your actual API credentials before use.


- Visit [Youtube-channel](https://www.youtube.com/@cartoonworld-y1d) for sample videos.