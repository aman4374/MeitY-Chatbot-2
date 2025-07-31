import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="MeitY Chatbot", layout="wide")
st.title("🤖 MeitY Knowledge Base Chatbot")

# --- NEW: Startup Diagnostics for Persistent Storage ---
with st.expander("System Status & Diagnostics"):
    PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
    st.write(f"Looking for persistent storage at: `{PERSISTENT_DIR}`")

    if os.path.exists(PERSISTENT_DIR):
        st.success(f"✅ Mount point `{PERSISTENT_DIR}` found.")
        
        # Check for expected index folders
        doc_index_path = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
        scraped_index_path = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
        youtube_index_path = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")

        if os.path.exists(doc_index_path):
            st.success("   - ✅ Document index found.")
        else:
            st.warning("   - ⚠️ Document index not found.")

        if os.path.exists(scraped_index_path):
            st.success("   - ✅ Scraped content index found.")
        else:
            st.warning("   - ⚠️ Scraped content index not found.")
        
        if os.path.exists(youtube_index_path):
            st.success("   - ✅ YouTube index found.")
        else:
            st.warning("   - ⚠️ YouTube index not found.")
            
    else:
        st.error(f"❌ Critical Error: Mount point `{PERSISTENT_DIR}` not found. The app cannot access its knowledge base.")
# --- END NEW ---


# Import the QA chain after running diagnostics
from backend.qa_chain import get_answer


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Chat Interface ---
st.info("Ask a question about the documents provided in the knowledge base.")
query = st.chat_input("Ask a question...")

if query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.spinner("Thinking..."):
        answer = get_answer(query)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

# --- Display Chat History ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])