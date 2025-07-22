import os
import whisper
from backend.utils import compute_md5, ensure_directory, split_text_into_chunks
# IMPORTANT: The two functions imported below (persist_to_faiss_video, is_video_already_ingested)
# must also be updated internally to use the new environment variable-based paths,
# specifically to locate the 'faiss_video' directory within 'persistent_storage'.
# (This was addressed in vector_store_video_faiss.py in the previous round)
from backend.vector_store_video_faiss import persist_to_faiss_video, is_video_already_ingested


# --- NEW: Define base path for persistent data ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# --- END NEW ---

# Constants - MODIFIED to use PERSISTENT_DIR
# This VIDEO_DIR is where the raw video files are temporarily stored before processing,
# or where they are uploaded to. It now correctly points to 'persistent_storage/video_upload'.
VIDEO_DIR = os.path.join(PERSISTENT_DIR, "video_upload")


def transcribe_video_to_text(video_path: str) -> str:
    """Transcribe audio from an MP4 video using Whisper."""
    try:
        model = whisper.load_model("base")  # or "medium"/"large" if you want higher accuracy
        result = model.transcribe(video_path)
        return result.get("text", "")
    except Exception as e:
        print(f"[Whisper Error] {e}")
        return ""

def ingest_video_file(video_path: str) -> str:
    # ensure_directory will now create 'persistent_storage/video_upload' if it doesn't exist
    ensure_directory(VIDEO_DIR)
    
    file_hash = compute_md5(video_path)
    
    # IMPORTANT: 'is_video_already_ingested' needs to internally know where
    # the 'faiss_video' data (which contains ingested hashes) is located,
    # specifically 'persistent_storage/faiss_video'.
    # (This is handled by the updated backend/vector_store_video_faiss.py)
    if is_video_already_ingested(file_hash):
        return "⚠️ Video already ingested (duplicate detected)."

    text = transcribe_video_to_text(video_path)
    if not text or len(text.strip()) < 30:
        return "❌ No valid transcription found in video."

    # IMPORTANT: 'persist_to_faiss_video' needs to internally know where
    # to save the FAISS index and related metadata for videos,
    # specifically 'persistent_storage/faiss_video'.
    # (This is handled by the updated backend/vector_store_video_faiss.py)
    persist_to_faiss_video(text, video_path, file_hash)
    return "✅ Video successfully transcribed and embedded."