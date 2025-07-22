import os
import tempfile
from yt_dlp import YoutubeDL
import whisper
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import SentenceTransformerEmbeddings
import warnings # Import the warnings module

# Suppress the specific FutureWarning from PyTorch about pickle deserialization
# This is safe to do for official Whisper models as you trust their source.
warnings.filterwarnings(
    "ignore",
    message="You are using `torch.load` with `weights_only=False`",
    category=FutureWarning
)

# --- NEW: Define base path for persistent data ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# --- END NEW ---

# Constants - MODIFIED to use PERSISTENT_DIR
# This correctly places 'video_upload' inside 'persistent_storage'
VIDEO_DIR = os.path.join(PERSISTENT_DIR, "video_upload")
# This correctly places 'faiss_video' inside 'persistent_storage'
FAISS_DIR = os.path.join(PERSISTENT_DIR, "faiss_video")

# Whisper model (load once)
# The warning should now be suppressed by the filterwarnings line
whisper_model = whisper.load_model("base")

def download_youtube_audio(youtube_url: str, output_path: str) -> str:
    # Ensure the output directory exists, which will be persistent_storage/video_upload
    os.makedirs(output_path, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "quiet": True
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        # Handle cases where yt_dlp might return different extensions before post-processing
        # Use info.get('filepath') if available, or construct from info
        filename = info.get('filepath')
        if not filename:
            # Fallback if 'filepath' isn't directly available or to ensure .mp3
            filename = ydl.prepare_filename(info)
            # Ensure it ends with .mp3 after post-processing
            base, _ = os.path.splitext(filename)
            filename = base + ".mp3"
        return filename


def transcribe_audio(path: str) -> str:
    result = whisper_model.transcribe(path)
    return result.get("text", "")

def ingest_youtube_video(youtube_url: str) -> str:
    try:
        print(f"📥 Downloading YouTube video: {youtube_url}")
        # VIDEO_DIR is already updated, so this will download into persistent_storage/video_upload
        audio_path = download_youtube_audio(youtube_url, VIDEO_DIR)
        print("🎙️ Transcribing...")
        transcript = transcribe_audio(audio_path)

        if not transcript.strip():
            # Clean up the downloaded audio file if transcription fails
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return "❌ Transcription failed or no speech detected."

        # Chunking
        chunks = [transcript[i:i+1000] for i in range(0, len(transcript), 1000)]
        docs = [Document(page_content=chunk, metadata={"source": youtube_url}) for chunk in chunks]

        # Save to FAISS
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

        # Ensure FAISS_DIR (persistent_storage/faiss_video) exists before loading/saving
        os.makedirs(FAISS_DIR, exist_ok=True)

        # Check if the FAISS index file exists within the FAISS_DIR
        faiss_index_file = os.path.join(FAISS_DIR, "index.faiss")
        if os.path.exists(faiss_index_file):
            print(f"Loading existing FAISS index from {FAISS_DIR}")
            # This already has allow_dangerous_deserialization=True
            vectordb = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
            vectordb.add_documents(docs)
        else:
            print(f"Creating new FAISS index in {FAISS_DIR}")
            vectordb = FAISS.from_documents(docs, embeddings)

        vectordb.save_local(FAISS_DIR)

        # Clean up the downloaded audio file after successful ingestion
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return "✅ YouTube video successfully transcribed and indexed."

    except Exception as e:
        print(f"An error occurred during YouTube video ingestion: {e}")
        # Attempt to clean up the audio file even on error if it was created
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)
        return f"❌ Failed to process YouTube video: {e}"