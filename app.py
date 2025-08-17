# import streamlit as st
# from dotenv import load_dotenv
# import os
# from backend.qa_chain import get_answer

# # Load environment variables
# load_dotenv()

# # --- Streamlit Page Config ---
# st.set_page_config(page_title="MeitY AI Agent", layout="wide")

# # --- Custom CSS Styling ---
# st.markdown("""
# <style>
#     .stApp { background-color: #1a1a2e; color: #e0e0e0; }
#     [data-testid="stSidebar"] { background-color: #162447; }
#     .stTextArea textarea { background-color: #2e2e48; color: #ffffff; border: 1px solid #4a4a6a; }
#     .stButton button {
#         background-color: #1f4068; color: #ffffff; border: 1px solid #1b263b;
#     }
#     .stButton button:hover {
#         background-color: #2c5d91; border-color: #1b263b; color: #ffffff;
#     }
#     [data-testid="stChatMessage"] {
#         background-color: #25253D;
#         border-radius: 0.5rem;
#         padding: 1rem;
#     }
# </style>
# """, unsafe_allow_html=True)

# # --- Sidebar ---
# with st.sidebar:
#     st.title("MeitY Knowledge Base AI Agent 💡")
#     st.markdown("---")
#     st.header("About")
#     st.markdown("""
#     This Generative AI Agent can answer queries based on documents, websites, and YouTube videos 
#     related to the Ministry of Electronics and IT (MeitY), Government of India.
#     """)
#     st.markdown("---")
#     st.header("Technologies Used")
#     st.markdown("""
#     - **LLM**: Together AI (Mistral)
#     - **Framework**: LangChain
#     - **Embeddings**: BAAI BGE
#     - **Vector Store**: FAISS
#     - **UI**: Streamlit
#     - **Fallback**: Tavily Search API
#     """)

# # --- Main Page Title ---
# st.markdown("""
#     <h2 style='text-align: center;'>
#         🗯️🇮🇳 MeitY Knowledge Base AI Agent
#     </h2>
# """, unsafe_allow_html=True)

# # --- Session State ---
# if "latest_query" not in st.session_state:
#     st.session_state.latest_query = ""
# if "latest_response" not in st.session_state:
#     st.session_state.latest_response = None

# # --- Query Form ---
# with st.form("query_form"):
#     query_text = st.text_area("Please enter your question here:", height=150)
#     submitted = st.form_submit_button("Submit")

# if submitted and query_text:
#     st.session_state.latest_query = query_text
#     with st.spinner("Generating answer..."):
#         st.session_state.latest_response = get_answer(query_text)

# # --- Show Response ---
# if st.session_state.latest_response:
#     st.markdown("---")
#     st.markdown(f"### Question:\n> {st.session_state.latest_query}")
    
#     response_data = st.session_state.latest_response
#     st.markdown("### Answer:")
#     st.write(response_data.get("answer", "No answer generated."))

#     source_docs = response_data.get("source_documents", [])
#     if source_docs:
#         st.markdown("### References:")
        
#         # Get the base path for persistent storage from environment variables
#         # This will be '/persistent_storage' on Azure and 'persistent_storage' locally
#         PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")

#         for i, doc in enumerate(source_docs[:5]):
#             source = doc.metadata.get("source", "Unknown Source")
            
#             # Check if the source is a local document path
#             is_local_doc = 'source_documents' in source.replace('\\', '/')

#             # Create a clean display name
#             filename = os.path.basename(source)
            
#             # --- MODIFIED LOGIC TO HANDLE AZURE PATHS ---
#             if is_local_doc:
#                 # Construct the full path to the file within the mounted storage on Azure
#                 # Example: /persistent_storage/source_documents/report.pdf
#                 azure_file_path = os.path.join(PERSISTENT_DIR, source)
                
#                 if os.path.exists(azure_file_path):
#                     with open(azure_file_path, "rb") as f:
#                         file_data = f.read()
                    
#                     st.download_button(
#                         label=f"[{i+1}]: Download {filename}",
#                         data=file_data,
#                         file_name=filename,
#                         key=f"file_{i}"
#                     )
#                 else:
#                     # Fallback if the file is not found in the Azure storage
#                     st.markdown(f"[{i+1}]: {filename} (Source file not available for download)")
            
#             else:  # It's a URL for scraped or YouTube content
#                 st.markdown(f"[{i+1}]: [{filename}]({source})")


import streamlit as st
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from backend.qa_chain import get_answer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="MeitY AI Agent", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "MeitY Knowledge Base AI Agent - Powered by RAG technology"
    }
)

# --- Custom CSS Styling (Original Color Scheme) ---
st.markdown("""
<style>
    .stApp { 
        background-color: #1a1a2e; 
        color: #e0e0e0; 
    }
    
    [data-testid="stSidebar"] { 
        background-color: #162447; 
        padding-top: 2rem;
    }
    
    .stTextArea textarea { 
        background-color: #2e2e48; 
        color: #ffffff; 
        border: 1px solid #4a4a6a;
        border-radius: 10px;
    }
    
    .stButton button {
        background-color: #1f4068; 
        color: #ffffff; 
        border: 1px solid #1b263b;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #2c5d91; 
        border-color: #1b263b; 
        color: #ffffff;
        transform: translateY(-2px);
    }
    
    [data-testid="stChatMessage"] {
        background-color: #25253D;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f4068;
    }
    
    .answer-container {
        background-color: #25253D;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        border-left: 4px solid #1f4068;
        color: #e0e0e0;
    }
    
    .source-card {
        background-color: #2e2e48;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4a90e2;
        color: #e0e0e0;
    }
    
    .query-display {
        background-color: #25253D;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #4a4a6a;
        color: #4a90e2;
        font-style: italic;
    }
    
    .main-title {
        text-align: center;
        color: #4a90e2;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .subtitle {
        text-align: center;
        color: #a0a0a0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_source_display(doc, index):
    """Format source document for clean display"""
    source = doc.metadata.get('source', 'Unknown Source')
    title = doc.metadata.get('title', '')
    
    # Determine source type and format accordingly
    if source.startswith('http'):
        source_type = "🌐 Web"
        display_name = source.split('/')[-1] or source
        if len(display_name) > 50:
            display_name = display_name[:47] + "..."
    elif os.path.exists(source):
        source_type = "📄 Document"
        display_name = os.path.basename(source)
    elif 'youtube' in source.lower() or 'youtu.be' in source.lower():
        source_type = "🎬 Video"
        display_name = title if title else "YouTube Video"
    else:
        source_type = "📋 Source"
        display_name = title if title else os.path.basename(source)
    
    return {
        'type': source_type,
        'name': display_name,
        'full_source': source,
        'title': title,
        'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
    }

# --- Sidebar (Keep Original) ---
with st.sidebar:
    st.markdown('<h1 style="color: #4a90e2;">🇮🇳 MeitY AI Agent</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # About Section
    st.header("📖 About")
    st.markdown("""
    This AI Agent provides answers using official MeitY documents, 
    websites, and multimedia content through advanced RAG technology.
    
    **Coverage Areas:**
    - 🏛️ MeitY Policies & Initiatives
    - 💻 Digital India Programs  
    - 🔒 Cybersecurity Guidelines
    - 📱 Technology Standards
    - 🌐 Digital Governance
    """)
    
    st.markdown("---")
    
    # Technology Stack
    with st.expander("🛠️ Tech Stack"):
        st.markdown("""
        - **LLM**: Together AI (Mistral-7B)
        - **Framework**: LangChain
        - **Embeddings**: BAAI BGE-Large
        - **Vector DB**: FAISS
        - **UI**: Streamlit
        - **Search**: Tavily API
        - **Processing**: Whisper, Playwright
        """)
    
    # Quick Stats
    st.markdown("---")
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    st.metric("Queries Processed", st.session_state.query_count)

# --- Main Page ---
st.markdown('<h1 class="main-title">🤖 MeitY Knowledge Base AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get instant answers about Ministry of Electronics and IT policies, initiatives, and digital governance</p>', unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "latest_query" not in st.session_state:
    st.session_state.latest_query = ""
if "latest_response" not in st.session_state:
    st.session_state.latest_response = None

# --- Query Input Section ---
st.markdown("### 💬 Ask Your Question")

# Sample questions for better UX
sample_questions = [
    "What are the key initiatives under Digital India?",
    "Tell me about MeitY's cybersecurity policies",
    "What is the National AI Portal about?",
    "Explain the IT Act amendments",
    "What are the recent updates in electronics manufacturing policy?"
]

# Quick question buttons
st.markdown("**Quick Questions:**")
cols = st.columns(3)
for i, question in enumerate(sample_questions[:3]):
    with cols[i]:
        if st.button(f"📝 {question[:30]}...", key=f"sample_{i}", help=question):
            st.session_state.sample_question = question

# Handle sample question selection
if 'sample_question' in st.session_state:
    query_text = st.session_state.sample_question
    del st.session_state.sample_question
else:
    query_text = st.text_area(
        "Enter your question about MeitY, Digital India, or related policies:",
        height=120,
        placeholder="Example: What are the main objectives of the National Digital Communications Policy?",
        help="Ask questions about Ministry of Electronics and IT policies, initiatives, or digital governance topics."
    )

# Submit button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submitted = st.button("🔍 Get Answer", type="primary", use_container_width=True)

# Process query
if submitted and query_text:
    st.session_state.latest_query = query_text
    st.session_state.query_count += 1
    
    # Show processing status
    with st.spinner("🔍 Searching knowledge base..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate progress updates
        import time
        for i, status in enumerate([
            "Checking local documents...",
            "Searching web content...", 
            "Analyzing video transcripts...",
            "Generating response..."
        ]):
            status_text.text(status)
            progress_bar.progress((i + 1) * 25)
            if i < 3:
                time.sleep(0.5)
        
        # Get the actual answer
        try:
            response = get_answer(query_text)
            st.session_state.latest_response = response
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            # Log technical details in backend (for monitoring)
            logger.info(f"Query processed successfully:")
            logger.info(f"  - Search Method: {response.get('search_method', 'unknown')}")
            logger.info(f"  - Tier: {response.get('tier', 'unknown')}")
            logger.info(f"  - Sources Found: {len(response.get('source_documents', []))}")
            if response.get('similarity_scores'):
                scores = response.get('similarity_scores', [])
                logger.info(f"  - Score Range: {min(scores):.3f} - {max(scores):.3f}")
            
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            st.session_state.latest_response = {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "source_documents": [],
                "tier": "Error",
                "search_method": "error"
            }
        finally:
            progress_bar.empty()
            status_text.empty()

# --- Display Response ---
if st.session_state.latest_response:
    st.markdown("---")
    
    # Query Display
    st.markdown(f"""
    <div class="query-display">
        <strong>🔍 Your Question:</strong> {st.session_state.latest_query}
    </div>
    """, unsafe_allow_html=True)
    
    response_data = st.session_state.latest_response
    answer_text = response_data.get("answer", "No answer generated.")
    
    # Display Answer (Clean, no technical details)
    st.markdown("### 📋 Answer")
    st.markdown(f"""
    <div class="answer-container">
        {answer_text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    # Display Top 5 Sources (Clean display)
    source_docs = response_data.get("source_documents", [])
    
    if source_docs:
        # Always show how many sources we have
        total_sources = len(source_docs)
        display_sources = min(5, total_sources)
        
        st.markdown(f"### 📚 Sources & References ({display_sources} of {total_sources})")
        
        # Ensure we show up to 5 sources
        top_sources = source_docs[:5]
        
        # Display each source with proper indexing
        for i, doc in enumerate(top_sources):
            source_info = format_source_display(doc, i)
            
            # Create expandable source card for better organization
            with st.expander(f"📋 Source {i + 1}: {source_info['type']} - {source_info['name']}", expanded=True):
                st.markdown(f"""
                <div class="source-card">
                    <p><strong>Content Preview:</strong></p>
                    <p style="font-style: italic; color: #a0a0a0;">{source_info['content_preview']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add download/view options
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # For local files, provide download
                    if os.path.exists(source_info['full_source']):
                        try:
                            with open(source_info['full_source'], "rb") as f:
                                file_data = f.read() 
                            
                            st.download_button(
                                label=f"📥 Download Document",
                                data=file_data,
                                file_name=os.path.basename(source_info['full_source']),
                                key=f"download_{i}",
                                help=f"Download: {source_info['name']}"
                            )
                        except Exception as e:
                            st.error(f"Unable to load file: {str(e)[:50]}...")
                
                with col2:
                    # For web sources, provide link
                    if source_info['full_source'].startswith('http'):
                        st.markdown(f"[🔗 View Online Source]({source_info['full_source']})")
                    elif not os.path.exists(source_info['full_source']):
                        st.info("📍 Internal Knowledge Base Reference")
        
        # Show summary of sources found
        if total_sources > 5:
            st.info(f"ℹ️ Showing top 5 most relevant sources. Total {total_sources} sources were found in the knowledge base.")
        else:
            st.success(f"All {total_sources} relevant sources are displayed above.")
    
    else:
        st.warning("⚠️ No source documents were found or returned. This might indicate an issue with the search system or that the query couldn't be matched to any content in the knowledge base.")
    
    # Add query to chat history (simplified)
    st.session_state.chat_history.append({
        "timestamp": datetime.now(),
        "query": st.session_state.latest_query,
        "answer_preview": answer_text[:100] + "..." if len(answer_text) > 100 else answer_text,
        "source_count": len(source_docs)
    })

# --- Chat History ---
if st.session_state.chat_history:
    with st.expander("📜 Recent Queries", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
            st.markdown(f"""
            **{entry['timestamp'].strftime('%H:%M:%S')}** - *{entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}*
            
            *{entry['answer_preview']}*
            """)
            st.markdown("---")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🇮🇳 <strong>MeitY Knowledge Base AI Agent</strong></p>
    <p>Powered by Advanced RAG Technology | Built for Ministry of Electronics and IT</p>
    <p><em>This system provides information based on official documents, websites, and multimedia content.</em></p>
</div>
""", unsafe_allow_html=True)  


import streamlit as st
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from backend.qa_chain import get_answer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="MeitY AI Agent", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "MeitY Knowledge Base AI Agent - Powered by RAG technology"
    }
)

# --- Custom CSS Styling (Original Color Scheme) ---
st.markdown("""
<style>
    .stApp { 
        background-color: #1a1a2e; 
        color: #e0e0e0; 
    }
    
    [data-testid="stSidebar"] { 
        background-color: #162447; 
        padding-top: 2rem;
    }
    
    .stTextArea textarea { 
        background-color: #2e2e48; 
        color: #ffffff; 
        border: 1px solid #4a4a6a;
        border-radius: 10px;
    }
    
    .stButton button {
        background-color: #1f4068; 
        color: #ffffff; 
        border: 1px solid #1b263b;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #2c5d91; 
        border-color: #1b263b; 
        color: #ffffff;
        transform: translateY(-2px);
    }
    
    [data-testid="stChatMessage"] {
        background-color: #25253D;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f4068;
    }
    
    .answer-container {
        background-color: #25253D;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        border-left: 4px solid #1f4068;
        color: #e0e0e0;
    }
    
    .source-card {
        background-color: #2e2e48;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4a90e2;
        color: #e0e0e0;
    }
    
    .query-display {
        background-color: #25253D;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #4a4a6a;
        color: #4a90e2;
        font-style: italic;
    }
    
    .main-title {
        text-align: center;
        color: #4a90e2;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .subtitle {
        text-align: center;
        color: #a0a0a0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_source_display(doc, index):
    """Format source document for clean display"""
    source = doc.metadata.get('source', 'Unknown Source')
    title = doc.metadata.get('title', '')
    
    # Determine source type and format accordingly
    if source.startswith('http'):
        source_type = "🌐 Web"
        display_name = source.split('/')[-1] or source
        if len(display_name) > 50:
            display_name = display_name[:47] + "..."
    elif 'youtube' in source.lower() or 'youtu.be' in source.lower():
        source_type = "🎬 Video"
        display_name = title if title else "YouTube Video"
    else:
        # For document sources, try to determine if it's a local file
        source_type = "📄 Document"
        display_name = title if title else os.path.basename(source)
    
    return {
        'type': source_type,
        'name': display_name,
        'full_source': source,
        'title': title,
        'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
    }

def find_document_file(source_path):
    """
    Try to find the document file in various possible locations for Azure deployment
    """
    if not source_path:
        return None
        
    # If it's a web URL, return None
    if source_path.startswith('http'):
        return None
        
    filename = os.path.basename(source_path)
    
    # Get current working directory for debugging
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    logger.info(f"Looking for file: {filename} (original path: {source_path})")
    
    # Possible locations where documents might be stored in Azure
    possible_paths = [
        source_path,  # Original path
        filename,  # Just filename in current directory
        os.path.join("documents", filename),  # documents folder
        os.path.join("data", filename),  # data folder
        os.path.join("persistent_storage", "documents", filename),  # persistent storage
        os.path.join("backend", "documents", filename),  # backend documents
        os.path.join("/tmp", filename),  # tmp directory
        os.path.join(".", "documents", filename),  # relative documents
        os.path.join(current_dir, "documents", filename),  # absolute documents
        os.path.join(current_dir, filename),  # current dir + filename
        # Add more Azure-specific paths
        os.path.join("/home", "site", "wwwroot", "documents", filename),
        os.path.join("/app", "documents", filename),
        os.path.join("persistent_storage", filename),
        # Try with source_documents folder structure
        os.path.join("source_documents", filename),
        os.path.join("persistent_storage", "source_documents", filename),
    ]
    
    # Also check if the filename contains path separators and try extracting just the name
    if "/" in filename or "\\" in filename:
        clean_filename = filename.split("/")[-1].split("\\")[-1]
        for base_path in ["", "documents", "data", "persistent_storage", "source_documents"]:
            if base_path:
                possible_paths.append(os.path.join(base_path, clean_filename))
            else:
                possible_paths.append(clean_filename)
    
    # Check each possible path
    for path in possible_paths:
        try:
            if os.path.exists(path) and os.path.isfile(path):
                logger.info(f"✅ Found document at: {path}")
                return path
            else:
                logger.debug(f"❌ Not found: {path}")
        except Exception as e:
            logger.debug(f"Error checking path {path}: {e}")
            continue
    
    # If still not found, list current directory contents for debugging
    try:
        logger.info(f"Directory contents of {current_dir}:")
        for item in os.listdir(current_dir):
            logger.info(f"  - {item}")
            
        # Also check if documents folder exists
        docs_path = os.path.join(current_dir, "documents")
        if os.path.exists(docs_path):
            logger.info(f"Contents of documents folder:")
            for item in os.listdir(docs_path):
                logger.info(f"  - documents/{item}")
                
        # Check persistent_storage folder
        persistent_path = os.path.join(current_dir, "persistent_storage")
        if os.path.exists(persistent_path):
            logger.info(f"Contents of persistent_storage folder:")
            for item in os.listdir(persistent_path):
                logger.info(f"  - persistent_storage/{item}")
                
    except Exception as e:
        logger.error(f"Error listing directory contents: {e}")
    
    logger.warning(f"❌ Could not find document file for: {source_path}")
    return None

# --- Sidebar (Keep Original) ---
with st.sidebar:
    st.markdown('<h1 style="color: #4a90e2;">🇮🇳 MeitY AI Agent</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # About Section
    st.header("📖 About")
    st.markdown("""
    This AI Agent provides answers using official MeitY documents, 
    websites, and multimedia content through advanced RAG technology.
    
    **Coverage Areas:**
    - 🏛️ MeitY Policies & Initiatives
    - 💻 Digital India Programs  
    - 🔒 Cybersecurity Guidelines
    - 📱 Technology Standards
    - 🌐 Digital Governance
    """)
    
    st.markdown("---")
    
    # Technology Stack
    with st.expander("🛠️ Tech Stack"):
        st.markdown("""
        - **LLM**: Together AI (Mistral-7B)
        - **Framework**: LangChain
        - **Embeddings**: BAAI BGE-Large
        - **Vector DB**: FAISS
        - **UI**: Streamlit
        - **Search**: Tavily API
        - **Processing**: Whisper, Playwright
        """)
    
    # Quick Stats
    st.markdown("---")
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    st.metric("Queries Processed", st.session_state.query_count)

# --- Main Page ---
st.markdown('<h1 class="main-title">🤖 MeitY Knowledge Base AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get instant answers about Ministry of Electronics and IT policies, initiatives, and digital governance</p>', unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "latest_query" not in st.session_state:
    st.session_state.latest_query = ""
if "latest_response" not in st.session_state:
    st.session_state.latest_response = None

# --- Query Input Section ---
st.markdown("### 💬 Ask Your Question")

# Sample questions for better UX
sample_questions = [
    "What are the key initiatives under Digital India?",
    "Tell me about MeitY's cybersecurity policies",
    "What is the National AI Portal about?",
    "Explain the IT Act amendments",
    "What are the recent updates in electronics manufacturing policy?"
]

# Quick question buttons
st.markdown("**Quick Questions:**")
cols = st.columns(3)
for i, question in enumerate(sample_questions[:3]):
    with cols[i]:
        if st.button(f"📝 {question[:30]}...", key=f"sample_{i}", help=question):
            st.session_state.sample_question = question

# Handle sample question selection
if 'sample_question' in st.session_state:
    query_text = st.session_state.sample_question
    del st.session_state.sample_question
else:
    query_text = st.text_area(
        "Enter your question about MeitY, Digital India, or related policies:",
        height=120,
        placeholder="Example: What are the main objectives of the National Digital Communications Policy?",
        help="Ask questions about Ministry of Electronics and IT policies, initiatives, or digital governance topics."
    )

# Submit button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submitted = st.button("🔍 Get Answer", type="primary", use_container_width=True)

# Process query
if submitted and query_text:
    st.session_state.latest_query = query_text
    st.session_state.query_count += 1
    
    # Show processing status
    with st.spinner("🔍 Searching knowledge base..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate progress updates
        import time
        for i, status in enumerate([
            "Checking local documents...",
            "Searching web content...", 
            "Analyzing video transcripts...",
            "Generating response..."
        ]):
            status_text.text(status)
            progress_bar.progress((i + 1) * 25)
            if i < 3:
                time.sleep(0.5)
        
        # Get the actual answer
        try:
            response = get_answer(query_text)
            st.session_state.latest_response = response
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            # Log technical details in backend (for monitoring)
            logger.info(f"Query processed successfully:")
            logger.info(f"  - Search Method: {response.get('search_method', 'unknown')}")
            logger.info(f"  - Tier: {response.get('tier', 'unknown')}")
            logger.info(f"  - Sources Found: {len(response.get('source_documents', []))}")
            if response.get('similarity_scores'):
                scores = response.get('similarity_scores', [])
                logger.info(f"  - Score Range: {min(scores):.3f} - {max(scores):.3f}")
            
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            st.session_state.latest_response = {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "source_documents": [],
                "tier": "Error",
                "search_method": "error"
            }
        finally:
            progress_bar.empty()
            status_text.empty()

# --- Display Response ---
if st.session_state.latest_response:
    st.markdown("---")
    
    # Query Display
    st.markdown(f"""
    <div class="query-display">
        <strong>🔍 Your Question:</strong> {st.session_state.latest_query}
    </div>
    """, unsafe_allow_html=True)
    
    response_data = st.session_state.latest_response
    answer_text = response_data.get("answer", "No answer generated.")
    
    # Display Answer (Clean, no technical details)
    st.markdown("### 📋 Answer")
    st.markdown(f"""
    <div class="answer-container">
        {answer_text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    # Display Top 5 Sources (Clean display)
    source_docs = response_data.get("source_documents", [])
    
    if source_docs:
        # Always show how many sources we have
        total_sources = len(source_docs)
        display_sources = min(5, total_sources)
        
        st.markdown(f"### 📚 Sources & References ({display_sources} of {total_sources})")
        
        # Ensure we show up to 5 sources
        top_sources = source_docs[:5]
        
        # Display each source with proper indexing
        for i, doc in enumerate(top_sources):
            source_info = format_source_display(doc, i)
            
            # Create expandable source card for better organization
            with st.expander(f"📋 Source {i + 1}: {source_info['type']} - {source_info['name']}", expanded=True):
                st.markdown(f"""
                <div class="source-card">
                    <p><strong>Content Preview:</strong></p>
                    <p style="font-style: italic; color: #a0a0a0;">{source_info['content_preview']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add download/view options
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # For local files, provide download
                    if os.path.exists(source_info['full_source']):
                        try:
                            with open(source_info['full_source'], "rb") as f:
                                file_data = f.read()
                            
                            st.download_button(
                                label=f"📥 Download Document",
                                data=file_data,
                                file_name=os.path.basename(source_info['full_source']),
                                key=f"download_{i}",
                                help=f"Download: {source_info['name']}"
                            )
                        except Exception as e:
                            st.error(f"Unable to load file: {str(e)[:50]}...")
                
                with col2:
                    # For web sources, provide link
                    if source_info['full_source'].startswith('http'):
                        st.markdown(f"[🔗 View Online Source]({source_info['full_source']})")
                    elif not os.path.exists(source_info['full_source']):
                        st.info("📍 Internal Knowledge Base Reference")
        
        # Show summary of sources found
        if total_sources > 5:
            st.info(f"ℹ️ Showing top 5 most relevant sources. Total {total_sources} sources were found in the knowledge base.")
        else:
            st.success(f"✅ All {total_sources} relevant sources are displayed above.")
    
    else:
        st.warning("⚠️ No source documents were found or returned. This might indicate an issue with the search system or that the query couldn't be matched to any content in the knowledge base.")
    
    # Add query to chat history (simplified)
    st.session_state.chat_history.append({
        "timestamp": datetime.now(),
        "query": st.session_state.latest_query,
        "answer_preview": answer_text[:100] + "..." if len(answer_text) > 100 else answer_text,
        "source_count": len(source_docs)
    })

# --- Chat History ---
if st.session_state.chat_history:
    with st.expander("📜 Recent Queries", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
            st.markdown(f"""
            **{entry['timestamp'].strftime('%H:%M:%S')}** - *{entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}*
            
            *{entry['answer_preview']}*
            """)
            st.markdown("---")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🇮🇳 <strong>MeitY Knowledge Base AI Agent</strong></p>
    <p>Powered by Advanced RAG Technology | Built for Ministry of Electronics and IT</p>
    <p><em>This system provides information based on official documents, websites, and multimedia content.</em></p>
</div>
""", unsafe_allow_html=True)