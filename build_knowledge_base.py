import os
import shutil
import re
import hashlib
import logging
from datetime import datetime  # ← This import was missing
from typing import List, Dict, Set
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from yt_dlp import YoutubeDL
import whisper
from playwright.sync_api import sync_playwright
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. CONFIGURATION ---
SOURCE_DOCS_DIR = "source_documents"

# Load URLs from file with better error handling
URLS_TO_SCRAPE = []
try:
    with open("urls_to_scrape.txt", "r", encoding='utf-8') as f:
        URLS_TO_SCRAPE = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    logger.info(f"Loaded {len(URLS_TO_SCRAPE)} URLs to scrape")
except FileNotFoundError:
    logger.warning("'urls_to_scrape.txt' not found. No websites will be scraped.")
except Exception as e:
    logger.error(f"Error reading urls_to_scrape.txt: {e}")

# YouTube URLs (you can also load these from a file)
YOUTUBE_URLS = ["https://www.youtube.com/watch?v=Bugs0dVcNI8&ab_channel=LangChain"]

# --- PATHS ---
PERSISTENT_DIR = "persistent_storage"
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")
COOKIE_FILE_PATH = os.path.join(PERSISTENT_DIR, 'cookies.txt')
SCRAPED_TEXT_DIR = os.path.join(PERSISTENT_DIR, "scraped_content")
YOUTUBE_TEXT_DIR = os.path.join(PERSISTENT_DIR, "youtube_transcripts")
HASH_LOG_PATH = os.path.join(PERSISTENT_DIR, 'processed_hashes.log')

# --- MODELS (Load once with error handling) ---
try:
    embeddings_model = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    logger.info("✅ Embeddings model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load embeddings model: {e}")
    raise

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]
)

# --- HASHING HELPER FUNCTIONS ---
def compute_md5_for_file(file_path: str) -> str:
    """Compute MD5 hash for a file."""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def compute_md5_for_text(text: str) -> str:
    """Compute MD5 hash for text content."""
    try:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for text: {e}")
        return ""

def load_processed_hashes(log_path: str) -> Set[str]:
    """Load previously processed hashes from log file."""
    if not os.path.exists(log_path):
        return set()
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            hashes = set(line.strip() for line in f if line.strip())
        logger.info(f"Loaded {len(hashes)} processed hashes from log")
        return hashes
    except Exception as e:
        logger.error(f"Error loading processed hashes: {e}")
        return set()

def save_processed_hashes(log_path: str, hashes_set: Set[str]) -> None:
    """Save processed hashes to log file."""
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            for h in sorted(hashes_set):
                f.write(h + '\n')
        logger.info(f"Saved {len(hashes_set)} hashes to log")
    except Exception as e:
        logger.error(f"Error saving processed hashes: {e}")

# --- ENHANCED BUILD FUNCTION ---
def build_faiss_index(docs_to_add: List[Document], index_path: str, index_name: str = "Unknown") -> None:
    """Builds or updates a FAISS index in batches with enhanced error handling."""
    
    if not docs_to_add:
        logger.info(f"No documents to add for {index_name} index")
        if not os.path.exists(index_path):
            os.makedirs(index_path, exist_ok=True)
        return

    try:
        # Split documents into chunks
        logger.info(f"Splitting {len(docs_to_add)} documents for {index_name}...")
        chunked_docs = text_splitter.split_documents(docs_to_add)
        logger.info(f"Created {len(chunked_docs)} chunks for {index_name} index")

        if not chunked_docs:
            logger.warning(f"No chunks created for {index_name} - documents may be empty")
            return

        batch_size = 256  # Adjust based on memory constraints
        
        # Check if index already exists
        faiss_file_path = os.path.join(index_path, "index.faiss")
        
        if os.path.exists(faiss_file_path):
            logger.info(f"Loading existing {index_name} index to add new documents...")
            try:
                vectordb = FAISS.load_local(index_path, embeddings_model, allow_dangerous_deserialization=True)
                
                # Add new documents in batches
                for i in tqdm(range(0, len(chunked_docs), batch_size), 
                            desc=f"Adding to {index_name} index"):
                    batch = chunked_docs[i:i+batch_size]
                    vectordb.add_documents(batch)
                    
            except Exception as e:
                logger.error(f"Error loading existing index for {index_name}: {e}")
                logger.info(f"Creating new index for {index_name}...")
                vectordb = None
        else:
            vectordb = None

        # Create new index if loading failed or doesn't exist
        if vectordb is None:
            logger.info(f"Creating new {index_name} index...")
            os.makedirs(index_path, exist_ok=True)
            
            # Create index in batches to handle large datasets
            for i in tqdm(range(0, len(chunked_docs), batch_size), 
                        desc=f"Building {index_name} index"):
                batch = chunked_docs[i:i+batch_size]
                
                if i == 0:
                    # Create initial index
                    vectordb = FAISS.from_documents(batch, embeddings_model)
                else:
                    # Add to existing index
                    vectordb.add_documents(batch)

        # Save the index
        vectordb.save_local(index_path)
        
        # Verify the save was successful
        if os.path.exists(faiss_file_path):
            logger.info(f"✅ {index_name} index successfully saved to {index_path}")
        else:
            logger.error(f"❌ Failed to save {index_name} index to {index_path}")
            
    except Exception as e:
        logger.error(f"Error building {index_name} index: {e}")
        raise

# --- ENHANCED PROCESSING FUNCTIONS ---

def process_local_documents(processed_hashes: Set[str]) -> List[Document]:
    """Process local documents with enhanced error handling and progress tracking."""
    logger.info("\n--- 📄 Processing Local Documents ---")
    
    if not os.path.exists(SOURCE_DOCS_DIR):
        logger.warning(f"Source documents directory not found: {SOURCE_DOCS_DIR}")
        return []
    
    docs_to_add = []
    files = [f for f in os.listdir(SOURCE_DOCS_DIR) if os.path.isfile(os.path.join(SOURCE_DOCS_DIR, f))]
    
    if not files:
        logger.info("No files found in source documents directory")
        return []
    
    supported_extensions = {'.pdf', '.docx', '.pptx'}
    skipped_files = []
    
    for filename in tqdm(files, desc="Processing local documents"):
        file_path = os.path.join(SOURCE_DOCS_DIR, filename)
        
        # Check if file extension is supported
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in supported_extensions:
            skipped_files.append(filename)
            continue
        
        try:
            file_hash = compute_md5_for_file(file_path)
            if not file_hash:
                logger.error(f"Could not compute hash for {filename}")
                continue
                
            if file_hash in processed_hashes:
                logger.debug(f"Skipping already processed file: {filename}")
                continue
            
            logger.info(f"Processing new file: {filename}")
            
            # Load document based on type
            docs = None
            if file_ext == ".pdf":
                docs = PyPDFLoader(file_path).load()
            elif file_ext == ".docx":
                docs = Docx2txtLoader(file_path).load()
            elif file_ext == ".pptx":
                docs = UnstructuredPowerPointLoader(file_path).load()
            
            if docs:
                # Add file info to metadata
                for doc in docs:
                    doc.metadata.update({
                        'source': file_path,
                        'filename': filename,
                        'file_type': file_ext[1:],  # Remove the dot
                        'processed_date': datetime.now().isoformat()
                    })
                
                docs_to_add.extend(docs)
                processed_hashes.add(file_hash)
                logger.info(f"✅ Successfully processed {filename} ({len(docs)} pages)")
            else:
                logger.warning(f"No content extracted from {filename}")
                
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue
    
    if skipped_files:
        logger.info(f"Skipped {len(skipped_files)} unsupported files: {skipped_files[:5]}{'...' if len(skipped_files) > 5 else ''}")
    
    logger.info(f"Processed {len(docs_to_add)} document pages from {len(files) - len(skipped_files)} files")
    return docs_to_add

def process_websites(processed_hashes: Set[str]) -> List[Document]:
    """Process websites with enhanced error handling and retry logic."""
    logger.info("\n--- 🌐 Processing Websites with Playwright ---")
    
    if not URLS_TO_SCRAPE:
        logger.info("No URLs to scrape")
        return []
    
    docs_to_add = []
    failed_urls = []
    
    try:
        with sync_playwright() as p:
            # Launch browser with better configuration
            browser = p.chromium.launch(
                headless=True,  # Set to True for production
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create context with realistic user agent
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            for url in tqdm(URLS_TO_SCRAPE, desc="Processing websites"):
                try:
                    logger.info(f"Processing URL: {url}")
                    page = context.new_page()
                    
                    # Navigate with timeout and wait for content
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Wait for dynamic content to load
                    page.wait_for_timeout(2000)
                    
                    # Get page content
                    html_content = page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Extract text
                    text = soup.get_text(separator='\n', strip=True)
                    
                    # Clean up text
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    text = '\n'.join(lines)
                    
                    if len(text.strip()) < 100:  # Skip if too little content
                        logger.warning(f"Insufficient content from {url} ({len(text)} chars)")
                        page.close()
                        continue
                    
                    # Check for duplicate content
                    content_hash = compute_md5_for_text(text)
                    if content_hash in processed_hashes:
                        logger.debug(f"Skipping duplicate content from {url}")
                        page.close()
                        continue
                    
                    # Get page title
                    try:
                        title = page.title() or url.split('/')[-1] or "Web Page"
                    except:
                        title = "Web Page"
                    
                    # Save scraped content
                    sanitized_filename = re.sub(r'[\\/*?:"<>|]', "_", url.replace('https://', '').replace('http://', '')) + ".txt"
                    content_file_path = os.path.join(SCRAPED_TEXT_DIR, sanitized_filename)
                    
                    try:
                        with open(content_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"URL: {url}\nTitle: {title}\n\n{text}")
                    except Exception as e:
                        logger.error(f"Error saving content for {url}: {e}")
                    
                    # Create document
                    doc = Document(
                        page_content=text,
                        metadata={
                            'source': url,
                            'title': title,
                            'content_type': 'web_page',
                            'scraped_date': datetime.now().isoformat(),
                            'content_length': len(text)
                        }
                    )
                    
                    docs_to_add.append(doc)
                    processed_hashes.add(content_hash)
                    
                    logger.info(f"✅ Successfully scraped {url} ({len(text)} chars)")
                    page.close()
                    
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    failed_urls.append(url)
                    try:
                        page.close()
                    except:
                        pass
                    continue
            
            context.close()
            browser.close()
            
    except Exception as e:
        logger.error(f"Critical error in web scraping: {e}")
        return docs_to_add
    
    if failed_urls:
        logger.warning(f"Failed to scrape {len(failed_urls)} URLs: {failed_urls[:3]}{'...' if len(failed_urls) > 3 else ''}")
    
    logger.info(f"Successfully scraped {len(docs_to_add)} websites")
    return docs_to_add

def process_youtube_videos(processed_hashes: Set[str]) -> List[Document]:
    """Process YouTube videos with enhanced error handling and cleanup."""
    logger.info("\n--- 🎬 Processing YouTube Videos ---")
    
    if not YOUTUBE_URLS:
        logger.info("No YouTube URLs to process")
        return []
    
    docs_to_add = []
    failed_videos = []
    
    # Create temporary directory for audio files
    audio_download_path = os.path.join(PERSISTENT_DIR, "youtube_audio")
    os.makedirs(audio_download_path, exist_ok=True)
    
    try:
        # Load Whisper model
        logger.info("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
        
        # Configure youtube-dl options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(audio_download_path, "%(id)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True
        }
        
        # Add cookies if available
        if os.path.exists(COOKIE_FILE_PATH):
            ydl_opts['cookiefile'] = COOKIE_FILE_PATH
            logger.info("Using cookies file for YouTube access")
        
        with YoutubeDL(ydl_opts) as ydl:
            for url in tqdm(YOUTUBE_URLS, desc="Processing YouTube videos"):
                audio_path = None
                try:
                    logger.info(f"Processing YouTube video: {url}")
                    
                    # Extract video info
                    info = ydl.extract_info(url, download=False)
                    video_id = info.get('id', 'unknown')
                    video_title = info.get('title', 'Unknown Video')
                    
                    logger.info(f"Video info: {video_title} ({video_id})")
                    
                    # Download audio
                    ydl.download([url])
                    
                    # Find the downloaded audio file
                    audio_path = os.path.join(audio_download_path, f"{video_id}.mp3")
                    
                    if not os.path.exists(audio_path):
                        # Try alternative extensions
                        for ext in ['mp3', 'wav', 'm4a', 'webm']:
                            alt_path = os.path.join(audio_download_path, f"{video_id}.{ext}")
                            if os.path.exists(alt_path):
                                audio_path = alt_path
                                break
                    
                    if not os.path.exists(audio_path):
                        logger.error(f"Could not find downloaded audio for {url}")
                        failed_videos.append(url)
                        continue
                    
                    # Transcribe audio
                    logger.info(f"Transcribing audio for {video_title}...")
                    result = whisper_model.transcribe(audio_path)
                    transcript = result["text"].strip()
                    
                    if len(transcript) < 50:  # Skip if transcript too short
                        logger.warning(f"Transcript too short for {url} ({len(transcript)} chars)")
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                        continue
                    
                    # Check for duplicate transcripts
                    transcript_hash = compute_md5_for_text(transcript)
                    if transcript_hash in processed_hashes:
                        logger.debug(f"Skipping duplicate transcript from {url}")
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                        continue
                    
                    # Save transcript
                    sanitized_filename = re.sub(r'[\\/*?:"<>|]', "_", video_title) + f"_{video_id}.txt"
                    transcript_file_path = os.path.join(YOUTUBE_TEXT_DIR, sanitized_filename)
                    
                    try:
                        with open(transcript_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"Title: {video_title}\nURL: {url}\nVideo ID: {video_id}\n\n{transcript}")
                    except Exception as e:
                        logger.error(f"Error saving transcript for {url}: {e}")
                    
                    # Create document
                    doc = Document(
                        page_content=transcript,
                        metadata={
                            'source': url,
                            'title': video_title,
                            'video_id': video_id,
                            'content_type': 'youtube_transcript',
                            'duration': info.get('duration', 0),
                            'transcribed_date': datetime.now().isoformat(),
                            'transcript_length': len(transcript)
                        }
                    )
                    
                    docs_to_add.append(doc)
                    processed_hashes.add(transcript_hash)
                    
                    logger.info(f"✅ Successfully processed {video_title} ({len(transcript)} chars)")
                    
                    # Clean up audio file
                    if audio_path and os.path.exists(audio_path):
                        os.remove(audio_path)
                        
                except Exception as e:
                    logger.error(f"Failed to process YouTube URL {url}: {e}")
                    failed_videos.append(url)
                    
                    # Clean up any remaining files
                    if audio_path and os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                    continue
                    
    except Exception as e:
        logger.error(f"Critical error in YouTube processing: {e}")
    
    finally:
        # Clean up temporary directory
        if os.path.exists(audio_download_path):
            try:
                shutil.rmtree(audio_download_path)
                logger.info("Cleaned up temporary audio files")
            except Exception as e:
                logger.error(f"Error cleaning up audio directory: {e}")
    
    if failed_videos:
        logger.warning(f"Failed to process {len(failed_videos)} videos: {failed_videos}")
    
    logger.info(f"Successfully processed {len(docs_to_add)} YouTube videos")
    return docs_to_add

def validate_system_requirements() -> Dict[str, bool]:
    """Validate that all required components are available."""
    requirements = {
        "source_documents_dir": os.path.exists(SOURCE_DOCS_DIR),
        "persistent_storage": True,  # Will be created if needed
        "playwright": False,
        "whisper": False,
        "embeddings_model": False
    }
    
    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        requirements["playwright"] = True
    except ImportError:
        logger.error("Playwright not available. Install with: pip install playwright && playwright install")
    
    # Check Whisper
    try:
        import whisper
        requirements["whisper"] = True
    except ImportError:
        logger.error("Whisper not available. Install with: pip install openai-whisper")
    
    # Check embeddings model
    try:
        embeddings_model.embed_query("test")
        requirements["embeddings_model"] = True
    except Exception as e:
        logger.error(f"Embeddings model not working: {e}")
    
    return requirements

def main():
    """Enhanced main function with better error handling and progress tracking."""
    logger.info("🚀 Starting MeitY Knowledge Base Builder")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    
    # Validate system requirements
    logger.info("🔍 Validating system requirements...")
    requirements = validate_system_requirements()
    
    failed_requirements = [req for req, status in requirements.items() if not status]
    if failed_requirements:
        logger.error(f"Missing requirements: {failed_requirements}")
        logger.error("Please install missing components before proceeding")
        return False
    
    logger.info("✅ All system requirements met")
    
    # Create necessary directories
    directories = [
        PERSISTENT_DIR,
        SCRAPED_TEXT_DIR,
        YOUTUBE_TEXT_DIR,
        DOC_FAISS_PATH,
        SCRAPED_FAISS_PATH,
        YOUTUBE_FAISS_PATH
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Load processed hashes
    processed_hashes = load_processed_hashes(HASH_LOG_PATH)
    initial_hash_count = len(processed_hashes)
    logger.info(f"📋 Loaded {initial_hash_count} previously processed items")
    
    # Process each data source
    processing_results = {}
    
    try:
        # Process local documents
        local_docs = process_local_documents(processed_hashes)
        processing_results['local_documents'] = len(local_docs)
        
        # Process websites
        web_docs = process_websites(processed_hashes)
        processing_results['websites'] = len(web_docs)
        
        # Process YouTube videos
        youtube_docs = process_youtube_videos(processed_hashes)
        processing_results['youtube_videos'] = len(youtube_docs)
        
        # Build FAISS indexes
        logger.info("\n--- 🔧 Building FAISS Indexes ---")
        
        build_faiss_index(local_docs, DOC_FAISS_PATH, "Local Documents")
        build_faiss_index(web_docs, SCRAPED_FAISS_PATH, "Scraped Websites")
        build_faiss_index(youtube_docs, YOUTUBE_FAISS_PATH, "YouTube Videos")
        
        # Save processed hashes
        save_processed_hashes(HASH_LOG_PATH, processed_hashes)
        
        # Summary
        new_items_count = len(processed_hashes) - initial_hash_count
        logger.info(f"\n--- ✅ Knowledge Base Build Complete ---")
        logger.info(f"📊 Processing Summary:")
        logger.info(f"   • Local Documents: {processing_results['local_documents']} processed")
        logger.info(f"   • Websites: {processing_results['websites']} processed")
        logger.info(f"   • YouTube Videos: {processing_results['youtube_videos']} processed")
        logger.info(f"   • Total New Items: {new_items_count}")
        logger.info(f"   • Total Items in Database: {len(processed_hashes)}")
        logger.info(f"⏰ Completed at: {datetime.now().isoformat()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error during knowledge base build: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)