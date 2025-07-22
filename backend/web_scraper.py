import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from backend.utils import compute_md5
from backend.vector_store_scraped_faiss import is_scraped_already, persist_to_faiss_scraped
from backend.utils import compute_md5_from_text

# --- NEW: Define base path for persistent data ---
# Get the base path for all persistent data from an environment variable.
# For local testing, it defaults to the 'persistent_storage' folder you created.
BASE_PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# --- END NEW ---

# MODIFIED: SCRAPED_DATA_DIR now points inside the persistent_storage folder
SCRAPED_DATA_DIR = os.path.join(BASE_PERSISTENT_DIR, "scraped_data")


def scrape_visible_text(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style/noscript content
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        visible_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in visible_text.splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Failed to scrape URL: {e}"

def scrape_and_ingest(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return "❌ Invalid URL"

    text = scrape_visible_text(url)
    if text.startswith("❌"):
        return text

    url_hash = compute_md5_from_text(text)  # ✅ MD5 of content

    # ✅ Check for duplicates
    # is_scraped_already relies on backend.vector_store_scraped_faiss,
    # which has already been updated to use the persistent_storage path.
    if is_scraped_already(url_hash):
        return "⚠️ URL already ingested (duplicate detected)."

    # ✅ Save raw scraped text for audit/debugging
    # os.makedirs will now create 'persistent_storage/scraped_data' if it doesn't exist
    os.makedirs(SCRAPED_DATA_DIR, exist_ok=True)
    with open(os.path.join(SCRAPED_DATA_DIR, f"{url_hash}.txt"), "w", encoding="utf-8") as f:
        f.write(text)

    # ✅ Embed into FAISS
    # persist_to_faiss_scraped relies on backend.vector_store_scraped_faiss,
    # which has already been updated to use the persistent_storage path.
    persist_to_faiss_scraped(text, url, url_hash)
    return "✅ Website scraped and embedded successfully."