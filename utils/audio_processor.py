import yt_dlp
from pydub import AudioSegment
import os
import glob
import shutil
import re

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_youtube_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|shorts\/|v\/|live\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_transcript(url_or_id: str) -> str:
    video_id = extract_youtube_video_id(url_or_id)
    if not video_id:
        return None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        data = None
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'hi', 'hi-Latn'])
                data = transcript.fetch()
            except Exception:
                # If specific language not found, take the first available transcript
                for t in transcript_list:
                    data = t.fetch()
                    break
        except Exception:
            pass

        if not data:
            try:
                data = YouTubeTranscriptApi().fetch(video_id)
            except Exception:
                data = YouTubeTranscriptApi.get_transcript(video_id)

        if not data:
            return None

        text_pieces = []
        for snippet in data:
            if hasattr(snippet, 'text'):
                text_pieces.append(snippet.text)
            elif isinstance(snippet, dict) and 'text' in snippet:
                text_pieces.append(snippet['text'])

        full_text = ' '.join(text_pieces).strip()
        return full_text if len(full_text) > 20 else None
    except Exception as e:
        print(f"Direct YouTube transcript unavailable: {e}")
        return None

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    js_runtimes = {}
    found_node = shutil.which("node")
    if found_node:
        js_runtimes["node"] = {"path": found_node}
    elif os.path.exists(r"C:\Program Files\nodejs\node.exe"):
        js_runtimes["node"] = {"path": r"C:\Program Files\nodejs\node.exe"}
    elif shutil.which("deno"):
        js_runtimes["deno"] = {"path": shutil.which("deno")}

    # Mobile clients to bypass 403 Forbidden datacenter bans on YouTube (without desktop header spoofing)
    client_strategies = [
        ["android", "ios"],
        ["ios", "web_safari"],
        ["tv_embedded"]
    ]

    last_error = None
    for clients in client_strategies:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "windowsfilenames": True,
            "restrictfilenames": True,
            "extractor_args": {
                "youtube": {
                    "player_client": clients,
                    "player_skip": ["webpage", "configs"]
                }
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }
        if js_runtimes:
            ydl_opts["js_runtimes"] = js_runtimes

        try:
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

                if filename and os.path.exists(filename) and os.path.getsize(filename) > 1000:
                    return filename
        except Exception as e:
            last_error = e
            continue

    audio_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.wav"))
    valid = [f for f in audio_files if os.path.getsize(f) > 1000]
    if valid:
        return max(valid, key=os.path.getmtime)

    raise RuntimeError(f"Failed to download audio from YouTube. Error: {last_error}")


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