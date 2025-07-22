import os
import json
from langchain_community.vectorstores import FAISS
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from backend.utils import compute_md5, split_text_into_chunks, ensure_directory

# --- NEW: Define base path for persistent data ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
BASE_PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# --- END NEW ---

# MODIFIED: Now PERSIST_DIR points inside the persistent_storage folder
PERSIST_DIR = os.path.join(BASE_PERSISTENT_DIR, "chroma_golden_faiss")
METADATA_FILE = os.path.join(PERSIST_DIR, "metadata.json")

# Ensure directory exists before trying to access files within it
# This will create 'persistent_storage/chroma_golden_faiss' if it doesn't exist.
ensure_directory(PERSIST_DIR)

# Load already ingested hashes
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "r") as f:
        INGESTED_HASHES = set(json.load(f))
else:
    INGESTED_HASHES = set()
    # Create the metadata file with an empty list if it doesn't exist
    with open(METADATA_FILE, "w") as f:
        json.dump([], f)

def is_already_ingested(file_hash: str) -> bool:
    return file_hash in INGESTED_HASHES

def persist_to_faiss_golden(text: str, file_path: str, file_hash: str):
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    chunks = split_text_into_chunks(text)
    docs = [Document(page_content=chunk, metadata={"source": os.path.basename(file_path), "hash": file_hash}) for chunk in chunks]

    # The FAISS.load_local and db.save_local functions will now correctly use the updated PERSIST_DIR
    if os.path.exists(os.path.join(PERSIST_DIR, "index.faiss")):
        db = FAISS.load_local(PERSIST_DIR, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embeddings)

    db.save_local(PERSIST_DIR)

    INGESTED_HASHES.add(file_hash)
    # The metadata file is also correctly saved within the new PERSIST_DIR
    with open(METADATA_FILE, "w") as f:
        json.dump(list(INGESTED_HASHES), f)

def load_faiss_golden(embeddings):
    # The index_path check also correctly points to the new PERSIST_DIR
    index_path = os.path.join(PERSIST_DIR, "index.faiss")
    if not os.path.exists(index_path):
        raise RuntimeError(f"❌ FAISS index not found at {PERSIST_DIR}. Please ingest at least one document.")

    # FAISS.load_local will correctly use the updated PERSIST_DIR
    return FAISS.load_local(PERSIST_DIR, embeddings, allow_dangerous_deserialization=True)