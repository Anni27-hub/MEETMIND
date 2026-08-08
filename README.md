# MeetMind 

 **Live Deployment**: [https://meetmind-qneltthz7vbc4wx3ug7qkl.streamlit.app](https://meetmind-qneltthz7vbc4wx3ug7qkl.streamlit.app)

MeetMind is a premium, high-speed **AI Meeting Intelligence Dashboard** designed to convert video and audio recordings into actionable corporate assets. Built with a sleek dark-themed interface, it allows users to process YouTube links or upload local audio/video files, generate high-accuracy transcripts, synthesize bulleted meeting summaries, extract decisions and tasks, and query the entire conversation context in real-time.

---

##  Key Features

- **Multi-Source Acquisition**: Seamless support for YouTube URLs and local file uploads (`mp3`, `mp4`, `wav`, `m4a`, `webm`).
- **High-Speed Transcription**: 
  - **English Mode**: Runs locally using optimized **Faster-Whisper** (`small`/`large-v2` configurations) with FP32/FP16 fallback.
  - **Hinglish Mode**: Routes through the **Sarvam AI Saaras API** to transcribe and translate mixed-language dialogues into English.
- **Executive Summarization & Insights**:
  - Automatically outlines a structured, bullet-pointed meeting summary.
  - Extracts key timeline decisions and pending open questions.
  - Creates action item lists with owners and deadlines.
- **Interactive RAG Chat Assistant**: Employs an in-memory **ChromaDB** vector store and **LangChain LCEL RAG chains** to let you chat directly with your transcript context.
- **Export & Reports Module**: One-click download of comprehensive summaries as Plaintext Markdown (`.txt`) or formal corporate PDFs formatted via `ReportLab`.
- **Ultra-Fast Startup**: Features fully lazy-loaded imports for heavy deep-learning dependencies (Whisper, PyTorch, LangChain, Transformers) to ensure the web dashboard boots up instantly.

---

##  Technology Stack

- **Frontend/Dashboard**: [Streamlit](https://streamlit.io/)
- **Orchestration**: [LangChain](https://www.langchain.com/) (LCEL Runnables)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Local Speech-to-Text**: [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2)
- **Hinglish STT / Translation**: [Sarvam AI](https://www.sarvam.ai/)
- **LLM Engine**: [Mistral AI](https://mistral.ai/) (`mistral-small-latest`)
- **PDF Generation**: [ReportLab](https://www.reportlab.com/)
- **Acquisition & Processing**: `yt-dlp`, `pydub` (FFmpeg)

---

##  Installation & Setup

### Prerequisites
- **Python**: version `3.10` or `3.11` recommended.
- **FFmpeg**: Required by `pydub` and `yt-dlp` for audio processing. Ensure `ffmpeg` and `ffprobe` are installed on your system and added to your system `PATH`.

### 1. Clone & Navigate to Project
```bash
git clone <your-repo-link>
cd "video agent"
```

### 2. Configure Environment Variables
Create a `.env` file in the root folder of the project:
```ini
# Mistral AI configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Speech-to-Text configuration
WHISPER_MODEL=small # Options: tiny, base, small, medium, large-v2

# Sarvam AI configuration (for Hinglish)
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_MODEL=saaras:v2.5
```

### 3. Setup Virtual Environment & Install Dependencies
It is highly recommended to use [uv](https://github.com/astral-sh/uv) or standard `pip` inside a virtual environment:

```bash
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install -r Requirements.txt
```

---

##  Running the Application

### Launch the Streamlit Web Dashboard
Run the following command within your active virtual environment:
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to access the dashboard.

### Run the CLI version
If you prefer running the pipeline inside your terminal:
```bash
python main.py
```

---

##  Project Architecture

```
├── app.py                  # Streamlit Web UI & Layout
├── main.py                 # CLI Interface & core pipeline coordinator
├── test.py                 # Standalone script for integration testing
├── Requirements.txt        # Package dependencies
├── .env                    # System API keys (ignored by git)
├── .gitignore              # Git ignore file
├── core/
│   ├── transcriber.py      # Speech-to-Text logic (Whisper/Sarvam)
│   ├── summarizer.py       # Map-Reduce summarization chains
│   ├── extractor.py        # Task/Decision/Question extraction
│   ├── rag_engine.py       # LCEL QA retrieval chains
│   └── vector_store.py     # ChromaDB instance management & HuggingFace embeddings
└── utils/
    └── audio_processor.py  # Youtube downloaders & audio format converter
```

---

##  Security Note

Make sure never to push your `.env` file containing private credentials to public Git repositories. The `.gitignore` included in this repository blocks it by default.
