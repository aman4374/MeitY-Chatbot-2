# import os
# import shutil
# import re
# from bs4 import BeautifulSoup
# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import SentenceTransformerEmbeddings
# from langchain.docstore.document import Document
# from yt_dlp import YoutubeDL
# import whisper
# import accelerate
# from playwright.sync_api import sync_playwright


# # --- 1. CONFIGURATION ---
# SOURCE_DOCS_DIR = "source_documents"

# # --- MODIFIED: Read URLs from a file ---
# try:
#     with open("urls_to_scrape.txt", "r") as f:
#         URLS_TO_SCRAPE = [line.strip() for line in f if line.strip()]
# except FileNotFoundError:
#     print("Warning: 'urls_to_scrape.txt' not found. No websites will be scraped.")
#     URLS_TO_SCRAPE = []
# # --- END MODIFICATION ---

# # Add the YouTube video URLs you want to transcribe here.
# YOUTUBE_URLS = [
#     # ... your youtube urls ...
# ]

# # ... rest of the script remains the same ...

# # --- PATHS ---
# PERSISTENT_DIR = "persistent_storage"
# DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
# SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
# YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")
# COOKIE_FILE_PATH = os.path.join(PERSISTENT_DIR, 'cookies.txt')
# # --- NEW: Paths for saving raw text for verification ---
# SCRAPED_TEXT_DIR = os.path.join(PERSISTENT_DIR, "scraped_content")
# YOUTUBE_TEXT_DIR = os.path.join(PERSISTENT_DIR, "youtube_transcripts")


# # --- MODELS (Load once) ---
# ##embeddings_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# embeddings_model = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# # --- HELPER FUNCTIONS ---
# def build_faiss_index(docs, index_path):
#     if not docs:
#         print(f"No documents provided for index: {index_path}. Skipping.")
#         if os.path.exists(index_path):
#             shutil.rmtree(index_path)
#         return

#     if os.path.exists(index_path):
#         print(f"Removing old index at {index_path}...")
#         shutil.rmtree(index_path)
    
#     os.makedirs(index_path)
#     chunked_docs = text_splitter.split_documents(docs)
#     print(f"Created {len(chunked_docs)} chunks. Building new index at {index_path}...")
#     vectordb = FAISS.from_documents(chunked_docs, embeddings_model)
#     vectordb.save_local(index_path)
#     print(f"✅ Index saved to {index_path}")

# # --- PROCESSING FUNCTIONS ---
# def process_local_documents():
#     # This function remains the same
#     print("\n--- 📄 Processing Local Documents ---")
#     docs = []
#     for filename in os.listdir(SOURCE_DOCS_DIR):
#         file_path = os.path.join(SOURCE_DOCS_DIR, filename)
#         try:
#             if filename.endswith(".pdf"):
#                 docs.extend(PyPDFLoader(file_path).load())
#             elif filename.endswith(".docx"):
#                 docs.extend(Docx2txtLoader(file_path).load())
#             elif filename.endswith(".pptx"):
#                 docs.extend(UnstructuredPowerPointLoader(file_path).load())
#         except Exception as e:
#             print(f"Error loading {filename}: {e}")
#     return docs

# # --- THIS FUNCTION IS UPDATED ---
# def process_websites():
#     print("\n--- 🌐 Processing Websites with Playwright ---")
#     docs = []
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         for url in URLS_TO_SCRAPE:
#             print(f"Scraping: {url}")
#             try:
#                 page = browser.new_page()
                
#                 # --- THIS LINE IS MODIFIED ---
#                 # Change 'networkidle' to 'load' and increase timeout to 60 seconds
#                 page.goto(url, wait_until="load", timeout=60000)
#                 # --- END OF MODIFICATION ---
                
#                 html_content = page.content()
#                 soup = BeautifulSoup(html_content, 'html.parser')
#                 text = soup.get_text(separator='\n', strip=True)

#                 sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", url) + ".txt"
#                 output_path = os.path.join(SCRAPED_TEXT_DIR, sanitized_filename)
#                 with open(output_path, 'w', encoding='utf-8') as f:
#                     f.write(text)
#                 print(f"   -> Saved scraped content to {output_path}")

#                 docs.append(Document(page_content=text, metadata={"source": url}))
#                 page.close()
#             except Exception as e:
#                 print(f"Failed to scrape {url}: {e}")
#                 continue
#         browser.close()
    
#     if docs:
#         build_faiss_index(docs, SCRAPED_FAISS_PATH)
#     else:
#         print("No websites successfully scraped.")
        
# def process_youtube_videos():
#     print("\n--- 🎬 Processing YouTube Videos ---")
#     whisper_model = whisper.load_model("base")
#     ydl_opts = { "format": "bestaudio/best", "outtmpl": os.path.join(PERSISTENT_DIR, "youtube_audio/%(id)s.%(ext)s"), "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}], "quiet": True }
#     if os.path.exists(COOKIE_FILE_PATH):
#         ydl_opts['cookiefile'] = COOKIE_FILE_PATH

#     docs = []
#     audio_download_path = os.path.join(PERSISTENT_DIR, "youtube_audio")
#     os.makedirs(audio_download_path, exist_ok=True)
    
#     with YoutubeDL(ydl_opts) as ydl:
#         for url in YOUTUBE_URLS:
#             try:
#                 info = ydl.extract_info(url, download=True)
#                 video_title = info.get('title', 'unknown_video')
                
#                 base, _ = os.path.splitext(ydl.prepare_filename(info))
#                 audio_path = base + ".mp3"
#                 transcript = whisper_model.transcribe(audio_path)["text"]
                
#                 # --- NEW: Save transcript to a file for verification ---
#                 sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", video_title) + ".txt"
#                 output_path = os.path.join(YOUTUBE_TEXT_DIR, sanitized_filename)
#                 with open(output_path, 'w', encoding='utf-8') as f:
#                     f.write(transcript)
#                 print(f"   -> Saved transcript to {output_path}")
#                 # --- END NEW ---

#                 docs.append(Document(page_content=transcript, metadata={"source": url}))
#             except Exception as e:
#                 print(f"Failed to process YouTube URL {url}: {e}")
#             finally:
#                 if 'audio_path' in locals() and os.path.exists(audio_path):
#                      os.remove(audio_path)
    
#     if os.path.exists(audio_download_path):
#         shutil.rmtree(audio_download_path)
#     return docs

# def main():
#     """Runs the full knowledge base creation pipeline."""
#     # --- NEW: Create verification directories ---
#     os.makedirs(PERSISTENT_DIR, exist_ok=True)
#     os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
#     os.makedirs(YOUTUBE_TEXT_DIR, exist_ok=True)
    
#     # 1. Gather all documents from all sources
#     local_docs = process_local_documents()
#     web_docs = process_websites()
#     youtube_docs = process_youtube_videos()
    
#     # 2. Build a separate index for each source
#     build_faiss_index(local_docs, DOC_FAISS_PATH)
#     build_faiss_index(web_docs, SCRAPED_FAISS_PATH)
#     build_faiss_index(youtube_docs, YOUTUBE_FAISS_PATH)

#     print("\n--- ✅ Knowledge Base Build Complete ---")

# if __name__ == "__main__":
#     main()


import os
import shutil
import re
import hashlib # <-- Re-added
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
from tqdm import tqdm

# --- 1. CONFIGURATION ---
SOURCE_DOCS_DIR = "source_documents"
try:
    with open("urls_to_scrape.txt", "r") as f:
        URLS_TO_SCRAPE = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Warning: 'urls_to_scrape.txt' not found. No websites will be scraped.")
    URLS_TO_SCRAPE = []
YOUTUBE_URLS = ["https://www.youtube.com/watch?v=Bugs0dVcNI8&ab_channel=LangChain"] # Add YouTube URLs here if needed

# --- PATHS ---
PERSISTENT_DIR = "persistent_storage"
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")
COOKIE_FILE_PATH = os.path.join(PERSISTENT_DIR, 'cookies.txt')
SCRAPED_TEXT_DIR = os.path.join(PERSISTENT_DIR, "scraped_content")
YOUTUBE_TEXT_DIR = os.path.join(PERSISTENT_DIR, "youtube_transcripts")
HASH_LOG_PATH = os.path.join(PERSISTENT_DIR, 'processed_hashes.log') # <-- NEW

# --- MODELS (Load once) ---
embeddings_model = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# --- NEW: HASHING HELPER FUNCTIONS ---
def compute_md5_for_file(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_md5_for_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def load_processed_hashes(log_path):
    if not os.path.exists(log_path):
        return set()
    with open(log_path, 'r') as f:
        return set(line.strip() for line in f)

def save_processed_hashes(log_path, hashes_set):
    with open(log_path, 'w') as f:
        for h in sorted(list(hashes_set)):
            f.write(h + '\n')

# --- UPDATED: Build function now supports incremental additions ---
def build_faiss_index(docs_to_add, index_path):
    """Builds or updates a FAISS index in batches."""
    if not docs_to_add:
        if not os.path.exists(index_path):
             os.makedirs(index_path)
        return

    chunked_docs = text_splitter.split_documents(docs_to_add)
    print(f"Created {len(chunked_docs)} new chunks for index at {index_path}...")

    batch_size = 256
    
    # --- MODIFIED: Check for the actual index.faiss file ---
    faiss_file_path = os.path.join(index_path, "index.faiss")
    if os.path.exists(faiss_file_path):
    # --- END MODIFICATION ---
        print(f"Loading existing index from {index_path} to add new documents...")
        vectordb = FAISS.load_local(index_path, embeddings_model, allow_dangerous_deserialization=True)
        # Add new documents in batches
        for i in tqdm(range(0, len(chunked_docs), batch_size), desc=f"Adding to index {os.path.basename(index_path)}"):
            vectordb.add_documents(chunked_docs[i:i+batch_size])
    else:
        # Create new index from scratch in batches
        if not os.path.exists(index_path):
            os.makedirs(index_path)
        vectordb = None
        for i in tqdm(range(0, len(chunked_docs), batch_size), desc=f"Building index {os.path.basename(index_path)}"):
            batch = chunked_docs[i:i+batch_size]
            if i == 0:
                vectordb = FAISS.from_documents(batch, embeddings_model)
            else:
                vectordb.add_documents(batch)

    vectordb.save_local(index_path)
    print(f"✅ Index updated and saved to {index_path}")

# --- PROCESSING FUNCTIONS (Updated with hashing logic) ---

def process_local_documents(processed_hashes):
    print("\n--- 📄 Processing Local Documents ---")
    docs_to_add = []
    for filename in tqdm(os.listdir(SOURCE_DOCS_DIR), desc="Checking local documents"):
        file_path = os.path.join(SOURCE_DOCS_DIR, filename)
        file_hash = compute_md5_for_file(file_path)
        
        if file_hash in processed_hashes:
            continue
            
        try:
            print(f"Processing new file: {filename}")
            if filename.endswith(".pdf"):
                docs_to_add.extend(PyPDFLoader(file_path).load())
            elif filename.endswith(".docx"):
                docs_to_add.extend(Docx2txtLoader(file_path).load())
            elif filename.endswith(".pptx"):
                docs_to_add.extend(UnstructuredPowerPointLoader(file_path).load())
            processed_hashes.add(file_hash)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    return docs_to_add

def process_websites(processed_hashes):
    print("\n--- 🌐 Processing Websites with Playwright ---")
    docs_to_add = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for url in tqdm(URLS_TO_SCRAPE, desc="Checking websites"):
            try:
                page = browser.new_page()
                page.goto(url, wait_until="load", timeout=60000)
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                
                content_hash = compute_md5_for_text(text)
                if content_hash in processed_hashes:
                    page.close()
                    continue

                print(f"Processing new website: {url}")
                sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", url) + ".txt"
                with open(os.path.join(SCRAPED_TEXT_DIR, sanitized_filename), 'w', encoding='utf-8') as f:
                    f.write(text)
                
                docs_to_add.append(Document(page_content=text, metadata={"source": url}))
                processed_hashes.add(content_hash)
                page.close()
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
        browser.close()
    return docs_to_add

def process_youtube_videos(processed_hashes):
    print("\n--- 🎬 Processing YouTube Videos ---")
    whisper_model = whisper.load_model("base")
    ydl_opts = { "format": "bestaudio/best", "outtmpl": os.path.join(PERSISTENT_DIR, "youtube_audio/%(id)s.%(ext)s"), "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}], "quiet": True }
    if os.path.exists(COOKIE_FILE_PATH):
        ydl_opts['cookiefile'] = COOKIE_FILE_PATH 
    docs_to_add = []
    audio_download_path = os.path.join(PERSISTENT_DIR, "youtube_audio")
    os.makedirs(audio_download_path, exist_ok=True)
    with YoutubeDL(ydl_opts) as ydl:
        for url in tqdm(YOUTUBE_URLS, desc="Checking YouTube videos"):
            try:
                info = ydl.extract_info(url, download=True)
                base, _ = os.path.splitext(ydl.prepare_filename(info))
                audio_path = base + ".mp3"
                transcript = whisper_model.transcribe(audio_path)["text"]
                
                transcript_hash = compute_md5_for_text(transcript)
                if transcript_hash in processed_hashes:
                    os.remove(audio_path)
                    continue

                print(f"Processing new YouTube video: {url}")
                video_title = info.get('title', 'unknown_video')
                sanitized_filename = re.sub(r'[\\/*?:"<>|]', "", video_title) + ".txt"
                with open(os.path.join(YOUTUBE_TEXT_DIR, sanitized_filename), 'w', encoding='utf-8') as f:
                    f.write(transcript)

                docs_to_add.append(Document(page_content=transcript, metadata={"source": url}))
                processed_hashes.add(transcript_hash)
                os.remove(audio_path)
            except Exception as e:
                print(f"Failed to process YouTube URL {url}: {e}")
    if os.path.exists(audio_download_path):
        shutil.rmtree(audio_download_path)
    return docs_to_add

def main():
    """Runs the full knowledge base creation pipeline."""
    os.makedirs(PERSISTENT_DIR, exist_ok=True)
    os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
    os.makedirs(YOUTUBE_TEXT_DIR, exist_ok=True)
    
    processed_hashes = load_processed_hashes(HASH_LOG_PATH)
    initial_hash_count = len(processed_hashes)
    print(f"Loaded {initial_hash_count} previously processed hashes.")
    
    local_docs_to_add = process_local_documents(processed_hashes)
    web_docs_to_add = process_websites(processed_hashes)
    youtube_docs_to_add = process_youtube_videos(processed_hashes)
    
    build_faiss_index(local_docs_to_add, DOC_FAISS_PATH)
    build_faiss_index(web_docs_to_add, SCRAPED_FAISS_PATH)
    build_faiss_index(youtube_docs_to_add, YOUTUBE_FAISS_PATH)

    save_processed_hashes(HASH_LOG_PATH, processed_hashes)
    new_hashes_count = len(processed_hashes) - initial_hash_count
    print(f"\nAdded {new_hashes_count} new items to the knowledge base.")
    print("--- ✅ Knowledge Base Build Complete ---")

if __name__ == "__main__":
    main() 

