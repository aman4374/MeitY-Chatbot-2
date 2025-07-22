import os
import json
from langchain_community.vectorstores import FAISS
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from backend.utils import compute_md5, split_text_into_chunks, ensure_directory
from backend.utils import compute_text_md5

# --- NEW: Define base path for persistent data ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
BASE_PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# --- END NEW ---

# MODIFIED: Now PERSIST_DIR points inside the persistent_storage folder
PERSIST_DIR = os.path.join(BASE_PERSISTENT_DIR, "chroma_scraped_faiss")
METADATA_FILE = os.path.join(PERSIST_DIR, "scraped_metadata.json")

# Ensure directory exists before trying to access files within it
# This will create 'persistent_storage/chroma_scraped_faiss' if it doesn't exist.
ensure_directory(PERSIST_DIR)

# Load already scraped hashes
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "r") as f:
        SCRAPED_HASHES = set(json.load(f))
else:
    SCRAPED_HASHES = set()
    # Create the metadata file with an empty list if it doesn't exist
    with open(METADATA_FILE, "w") as f:
        json.dump([], f)

def is_scraped_already(text: str) -> bool:
    """Compute hash of scraped text to avoid reprocessing."""
    content_hash = compute_text_md5(text)
    # This check relies on SCRAPED_HASHES, which is loaded from METADATA_FILE
    # METADATA_FILE's path is now correctly within PERSIST_DIR
    return content_hash in SCRAPED_HASHES

def persist_to_faiss_scraped(text: str, source_url: str, url_hash: str):
    """Embed and persist scraped text content into FAISS."""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    chunks = split_text_into_chunks(text)
    docs = [Document(page_content=chunk, metadata={"source": source_url, "hash": url_hash}) for chunk in chunks]

    # Load existing DB or create new - now correctly uses the updated PERSIST_DIR
    if os.path.exists(os.path.join(PERSIST_DIR, "index.faiss")):
        db = FAISS.load_local(PERSIST_DIR, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embeddings)

    db.save_local(PERSIST_DIR)

    # Save hash to avoid re-scraping - now correctly updates METADATA_FILE within PERSIST_DIR
    SCRAPED_HASHES.add(url_hash)
    with open(METADATA_FILE, "w") as f:
        json.dump(list(SCRAPED_HASHES), f)

def load_faiss_scraped(embeddings):
    # index_path check now correctly points to the new PERSIST_DIR
    index_path = os.path.join(PERSIST_DIR, "index.faiss")
    if not os.path.exists(index_path):
        raise RuntimeError(f"❌ FAISS index for scraped data not found at {PERSIST_DIR}. Scrape and ingest at least one URL.")

    # FAISS.load_local will correctly use the updated PERSIST_DIR
    return FAISS.load_local(PERSIST_DIR, embeddings, allow_dangerous_deserialization=True)