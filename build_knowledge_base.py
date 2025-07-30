import os
import shutil
import re
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from yt_dlp import YoutubeDL
import whisper
import accelerate
from playwright.sync_api import sync_playwright

# --- 1. CONFIGURATION ---
SOURCE_DOCS_DIR = "source_documents"
URLS_TO_SCRAPE = [
    
]
YOUTUBE_URLS = [
    
]

# --- PATHS ---
PERSISTENT_DIR = "persistent_storage"
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")
COOKIE_FILE_PATH = os.path.join(PERSISTENT_DIR, 'cookies.txt')
# --- NEW: Paths for saving raw text for verification ---
SCRAPED_TEXT_DIR = os.path.join(PERSISTENT_DIR, "scraped_content")
YOUTUBE_TEXT_DIR = os.path.join(PERSISTENT_DIR, "youtube_transcripts")


# --- MODELS (Load once) ---
embeddings_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# --- HELPER FUNCTIONS ---
def build_faiss_index(docs, index_path):
    if not docs:
        print(f"No documents provided for index: {index_path}. Skipping.")
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
        return

    if os.path.exists(index_path):
        print(f"Removing old index at {index_path}...")
        shutil.rmtree(index_path)
    
    os.makedirs(index_path)
    chunked_docs = text_splitter.split_documents(docs)
    print(f"Created {len(chunked_docs)} chunks. Building new index at {index_path}...")
    vectordb = FAISS.from_documents(chunked_docs, embeddings_model)
    vectordb.save_local(index_path)
    print(f"✅ Index saved to {index_path}")

# --- PROCESSING FUNCTIONS ---
def process_local_documents():
    # This function remains the same
    print("\n--- 📄 Processing Local Documents ---")
    docs = []
    for filename in os.listdir(SOURCE_DOCS_DIR):
        file_path = os.path.join(SOURCE_DOCS_DIR, filename)
        try:
            if filename.endswith(".pdf"):
                docs.extend(PyPDFLoader(file_path).load())
            elif filename.endswith(".docx"):
                docs.extend(Docx2txtLoader(file_path).load())
            elif filename.endswith(".pptx"):
                docs.extend(UnstructuredPowerPointLoader(file_path).load())
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    return docs

# --- THIS FUNCTION IS UPDATED ---
def process_websites():
    print("\n--- 🌐 Processing Websites with Playwright ---")
    docs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for url in URLS_TO_SCRAPE:
            print(f"Scraping: {url}")
            try:
                page = browser.new_page()
                
                # --- THIS LINE IS MODIFIED ---
                # Change 'networkidle' to 'load' and increase timeout to 60 seconds
                page.goto(url, wait_until="load", timeout=60000)
                # --- END OF MODIFICATION ---
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)

                sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", url) + ".txt"
                output_path = os.path.join(SCRAPED_TEXT_DIR, sanitized_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   -> Saved scraped content to {output_path}")

                docs.append(Document(page_content=text, metadata={"source": url}))
                page.close()
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
                continue
        browser.close()
    
    if docs:
        build_faiss_index(docs, SCRAPED_FAISS_PATH)
    else:
        print("No websites successfully scraped.")
        
def process_youtube_videos():
    print("\n--- 🎬 Processing YouTube Videos ---")
    whisper_model = whisper.load_model("base")
    ydl_opts = { "format": "bestaudio/best", "outtmpl": os.path.join(PERSISTENT_DIR, "youtube_audio/%(id)s.%(ext)s"), "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}], "quiet": True }
    if os.path.exists(COOKIE_FILE_PATH):
        ydl_opts['cookiefile'] = COOKIE_FILE_PATH

    docs = []
    audio_download_path = os.path.join(PERSISTENT_DIR, "youtube_audio")
    os.makedirs(audio_download_path, exist_ok=True)
    
    with YoutubeDL(ydl_opts) as ydl:
        for url in YOUTUBE_URLS:
            try:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'unknown_video')
                
                base, _ = os.path.splitext(ydl.prepare_filename(info))
                audio_path = base + ".mp3"
                transcript = whisper_model.transcribe(audio_path)["text"]
                
                # --- NEW: Save transcript to a file for verification ---
                sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", video_title) + ".txt"
                output_path = os.path.join(YOUTUBE_TEXT_DIR, sanitized_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"   -> Saved transcript to {output_path}")
                # --- END NEW ---

                docs.append(Document(page_content=transcript, metadata={"source": url}))
            except Exception as e:
                print(f"Failed to process YouTube URL {url}: {e}")
            finally:
                if 'audio_path' in locals() and os.path.exists(audio_path):
                     os.remove(audio_path)
    
    if os.path.exists(audio_download_path):
        shutil.rmtree(audio_download_path)
    return docs

def main():
    """Runs the full knowledge base creation pipeline."""
    # --- NEW: Create verification directories ---
    os.makedirs(PERSISTENT_DIR, exist_ok=True)
    os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
    os.makedirs(YOUTUBE_TEXT_DIR, exist_ok=True)
    
    # 1. Gather all documents from all sources
    local_docs = process_local_documents()
    web_docs = process_websites()
    youtube_docs = process_youtube_videos()
    
    # 2. Build a separate index for each source
    build_faiss_index(local_docs, DOC_FAISS_PATH)
    build_faiss_index(web_docs, SCRAPED_FAISS_PATH)
    build_faiss_index(youtube_docs, YOUTUBE_FAISS_PATH)

    print("\n--- ✅ Knowledge Base Build Complete ---")

if __name__ == "__main__":
    main()