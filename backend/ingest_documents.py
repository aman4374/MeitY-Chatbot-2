import os
from backend.utils import compute_md5, extract_text_from_file
# IMPORTANT: The two functions imported below must also be updated internally
# to use the new environment variable-based paths.
# (This was addressed in vector_store_golden_faiss.py in the previous round)
from backend.vector_store_golden_faiss import persist_to_faiss_golden, is_already_ingested

# --- NEW: Define paths for cloud deployment ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")

# Construct the full path for the golden FAISS index using the folder name from your screenshot.
# This correctly points to 'persistent_storage/chroma_golden_faiss'
GOLDEN_FAISS_PATH = os.path.join(PERSISTENT_DIR, "chroma_golden_faiss")
# --- END NEW ---


def ingest_file(file_path: str) -> str:
    """Ingests a file, checks for duplicates, and persists its embeddings.
    Note: The 'file_path' argument for this function is expected to be
    the full path to the uploaded file, which should ideally be within
    'persistent_storage/uploads' in your new structure. This function
    itself doesn't define the 'uploads' directory, but consumes the path provided.
    """
    file_hash = compute_md5(file_path)

    # --- MODIFIED: Use the new dynamic path ---
    # Construct the full path to the specific FAISS index file.
    index_file_path = os.path.join(GOLDEN_FAISS_PATH, "index.faiss")

    # Check if the file's content (via its hash) and the index file already exist.
    # 'is_already_ingested' and 'persist_to_faiss_golden' are assumed to be updated
    # in 'backend/vector_store_golden_faiss.py' to use GOLDEN_FAISS_PATH.
    if is_already_ingested(file_hash) and os.path.exists(index_file_path):
    # --- END MODIFIED ---
        return "⚠️ File already ingested (duplicate detected)."

    # Extract text from the file.
    text = extract_text_from_file(file_path)
    if not text or len(text.strip()) < 20:
        return "❌ No readable content found in the file." 

    # Persist the extracted text to the FAISS vector store.
    # The 'persist_to_faiss_golden' function is responsible for using GOLDEN_FAISS_PATH to save the data.
    persist_to_faiss_golden(text, file_path, file_hash)
    
    return "✅ Document successfully embedded and saved."