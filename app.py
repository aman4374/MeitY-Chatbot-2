import streamlit as st
from backend.ingest_documents import ingest_file
# FIX: Reverted the import name for the web scraper module
from backend.web_scraper import scrape_and_ingest # This assumes your file is named web_scraper.py
from backend.ingest_video import ingest_video_file
from backend.ingest_video_youtube import ingest_youtube_video
from backend.qa_chain import get_answer
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="MeitY RAG Chatbot", layout="wide")
st.title("🤖 MeitY RAG Chatbot | Docs + Web + Video + YouTube")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Define base path for persistent data ---
BASE_PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")

# Define specific upload directories within the persistent storage
UPLOAD_DOCS_DIR = os.path.join(BASE_PERSISTENT_DIR, "uploads")
UPLOAD_VIDEOS_DIR = os.path.join(BASE_PERSISTENT_DIR, "video_upload")

# Ensure these directories exist
os.makedirs(UPLOAD_DOCS_DIR, exist_ok=True)
os.makedirs(UPLOAD_VIDEOS_DIR, exist_ok=True)
# --- END NEW ---

# ------------------ 📤 Document Upload ------------------
uploaded_file = st.file_uploader("Upload PDF, DOCX, or PPTX", type=["pdf", "docx", "pptx"])
if st.button("📥 Ingest Document") and uploaded_file:
    with st.spinner("Processing uploaded document..."):
        doc_path = os.path.join(UPLOAD_DOCS_DIR, uploaded_file.name)
        with open(doc_path, "wb") as f:
            f.write(uploaded_file.read())
        
        result = ingest_file(doc_path)
        st.success(result)

# ------------------ 🌐 Web Scraping ------------------
url_input = st.text_input("Enter website URL to scrape:")
if st.button("Scrape"):
    url = url_input.strip()
    
    if url == "" or not url.startswith("http"):
        st.error("❌ Please enter a valid URL starting with http or https.")
    else:
        status = scrape_and_ingest(url)
        if status:
            st.success("✅ Successfully scraped and ingested content.")
        else:
            st.error("❌ Failed to scrape the provided URL.")


# ------------------ 🎥 Local Video Upload ------------------
video_file = st.file_uploader("🎥 Upload MP4 video", type=["mp4"])
if st.button("🎙️ Transcribe & Ingest Video") and video_file:
    with st.spinner("Transcribing and embedding video..."):
        video_path = os.path.join(UPLOAD_VIDEOS_DIR, video_file.name)
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        
        status = ingest_video_file(video_path)
        st.success(status)

# ------------------ 📺 YouTube Ingestion ------------------
youtube_url = st.text_input("📺 Enter YouTube Video URL")
if st.button("📡 Ingest YouTube Video"):
    with st.spinner("Transcribing and embedding YouTube content..."):
        result = ingest_youtube_video(youtube_url)
        st.success(result)

# ------------------ 💬 Chat ------------------
query = st.text_input("🧠 Ask a question:")
if st.button("🔍 Get Answer") and query:
    with st.spinner("Thinking..."):
        answer = get_answer(query)
        st.session_state.chat_history.append((query, answer))
        st.markdown(f"### 📘 AI Response:\n{answer}", unsafe_allow_html=False)

# ------------------ 🕘 Chat History ------------------
if st.session_state.chat_history:
    st.subheader("🕘 Chat History")
    for q, a in st.session_state.chat_history:
        st.markdown(f"**🧾 Question:** {q}")
        st.markdown(f"{a}")
        st.markdown("---")

# import streamlit as st
# import sys
# import platform

# st.set_page_config(page_title="Azure Test App", layout="wide")
# st.title("✅ Success! Your Azure App Service is Working.")
# st.write("This is a minimal Streamlit application.")
# st.info(f"Python Version: {sys.version}")
# st.info(f"Platform: {platform.platform()}")
# st.balloons()