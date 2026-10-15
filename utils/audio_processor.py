import yt_dlp
from pydub import AudioSegment
import os
import glob
import shutil

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR,exist_ok = True)

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    node_path = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

    ydl_opts = {
        "format": "bestaudio[language*=en]/bestaudio[format_id*=en]/bestaudio/best",
        "outtmpl": output_path,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "js_runtimes": {"node": {"path": node_path}} if os.path.exists(node_path) else ["node"],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": False,
        "no_warnings": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.youtube.com/",
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        vid_id = info.get("id")

        filename = None
        if vid_id:
            expected = os.path.join(DOWNLOAD_DIR, f"{vid_id}.wav")
            if os.path.exists(expected) and os.path.getsize(expected) > 1000:
                filename = expected

        if not filename and "requested_downloads" in info and info["requested_downloads"]:
            candidate = info["requested_downloads"][0].get("filepath")
            if candidate and os.path.exists(candidate) and os.path.getsize(candidate) > 1000:
                filename = candidate

        if not filename or not os.path.exists(filename):
            base_path = os.path.splitext(ydl.prepare_filename(info))[0]
            for ext in [".wav", ".m4a", ".mp3", ".webm", ".mp4"]:
                if os.path.exists(base_path + ext) and os.path.getsize(base_path + ext) > 1000:
                    filename = base_path + ext
                    break

        if not filename or not os.path.exists(filename):
            audio_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.wav"))
            valid = [f for f in audio_files if os.path.getsize(f) > 1000]
            if valid:
                filename = max(valid, key=os.path.getmtime)

    if not filename or not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        raise RuntimeError("Failed to download a valid audio file from YouTube.")

    return filename


#data = download_youtube_audio("https://www.youtube.com/watch?v=1FqcgtsWCbY")


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz  1 is for monoaudio
    audio.export(output_path, format="wav")
    return output_path

#data_final = convert_to_wav(data)



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list: #for large audio files we need to chunk them into smaller pieces
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000  # bcz of milliseconds example - 10 mins= 10 * 60 * 1000 = 600000 miliseconds

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

#print(chunk_audio(data_final))

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks