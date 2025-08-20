# import streamlit as st
# from dotenv import load_dotenv
# import os
# import logging
# from datetime import datetime
# from backend.qa_chain import get_answer

# # Load environment variables
# load_dotenv()

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- Streamlit Page Config ---
# st.set_page_config(
#     page_title="MeitY AI Agent", 
#     layout="wide",
#     initial_sidebar_state="expanded",
#     menu_items={
#         'About': "MeitY Knowledge Base AI Agent - Powered by RAG technology"
#     }
# )

# # --- Custom CSS Styling (Original Color Scheme) ---
# st.markdown("""
# <style>
#     .stApp { 
#         background-color: #1a1a2e; 
#         color: #e0e0e0; 
#     }
    
#     [data-testid="stSidebar"] { 
#         background-color: #162447; 
#         padding-top: 2rem;
#     }
    
#     .stTextArea textarea { 
#         background-color: #2e2e48; 
#         color: #ffffff; 
#         border: 1px solid #4a4a6a;
#         border-radius: 10px;
#     }
    
#     .stButton button {
#         background-color: #1f4068; 
#         color: #ffffff; 
#         border: 1px solid #1b263b;
#         border-radius: 10px;
#         font-weight: bold;
#         transition: all 0.3s ease;
#     }
    
#     .stButton button:hover {
#         background-color: #2c5d91; 
#         border-color: #1b263b; 
#         color: #ffffff;
#         transform: translateY(-2px);
#     }
    
#     [data-testid="stChatMessage"] {
#         background-color: #25253D;
#         border-radius: 15px;
#         padding: 1.5rem;
#         margin: 1rem 0;
#         border-left: 4px solid #1f4068;
#     }
    
#     .answer-container {
#         background-color: #25253D;
#         border-radius: 15px;
#         padding: 2rem;
#         margin: 2rem 0;
#         border-left: 4px solid #1f4068;
#         color: #e0e0e0;
#     }
    
#     .source-card {
#         background-color: #2e2e48;
#         border-radius: 10px;
#         padding: 1rem;
#         margin: 0.5rem 0;
#         border-left: 3px solid #4a90e2;
#         color: #e0e0e0;
#     }
    
#     .query-display {
#         background-color: #25253D;
#         border-radius: 10px;
#         padding: 1rem;
#         margin: 1rem 0;
#         border: 1px solid #4a4a6a;
#         color: #4a90e2;
#         font-style: italic;
#     }
    
#     .main-title {
#         text-align: center;
#         color: #4a90e2;
#         font-size: 2.5rem;
#         margin-bottom: 2rem;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
#     }
    
#     .subtitle {
#         text-align: center;
#         color: #a0a0a0;
#         font-size: 1.1rem;
#         margin-bottom: 2rem;
#     }
# </style>
# """, unsafe_allow_html=True)

# # --- Helper Functions ---
# def format_source_display(doc, index):
#     """Format source document for clean display"""
#     source = doc.metadata.get('source', 'Unknown Source')
#     title = doc.metadata.get('title', '')
    
#     # Determine source type and format accordingly
#     if source.startswith('http'):
#         source_type = "🌐 Web"
#         display_name = source.split('/')[-1] or source
#         if len(display_name) > 50:
#             display_name = display_name[:47] + "..."
#     elif os.path.exists(source):
#         source_type = "📄 Document"
#         display_name = os.path.basename(source)
#     elif 'youtube' in source.lower() or 'youtu.be' in source.lower():
#         source_type = "🎬 Video"
#         display_name = title if title else "YouTube Video"
#     else:
#         source_type = "📋 Source"
#         display_name = title if title else os.path.basename(source)
    
#     return {
#         'type': source_type,
#         'name': display_name,
#         'full_source': source,
#         'title': title,
#         'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
#     }

# # --- Sidebar (Keep Original) ---
# with st.sidebar:
#     st.markdown('<h1 style="color: #4a90e2;">🇮🇳 MeitY AI Agent</h1>', unsafe_allow_html=True)
#     st.markdown("---")
    
#     # About Section
#     st.header("📖 About")
#     st.markdown("""
#     This AI Agent provides answers using official MeitY documents, 
#     websites, and multimedia content through advanced RAG technology.
    
#     **Coverage Areas:**
#     - 🏛️ MeitY Policies & Initiatives
#     - 💻 Digital India Programs  
#     - 🔒 Cybersecurity Guidelines
#     - 📱 Technology Standards
#     - 🌐 Digital Governance
#     """)
    
#     st.markdown("---")
    
#     # Technology Stack
#     with st.expander("🛠️ Tech Stack"):
#         st.markdown("""
#         - **LLM**: Together AI (Mistral-7B)
#         - **Framework**: LangChain
#         - **Embeddings**: BAAI BGE-Large
#         - **Vector DB**: FAISS
#         - **UI**: Streamlit
#         - **Search**: Tavily API
#         - **Processing**: Whisper, Playwright
#         """)
    
#     # Quick Stats
#     st.markdown("---")
#     if 'query_count' not in st.session_state:
#         st.session_state.query_count = 0
    
#     st.metric("Queries Processed", st.session_state.query_count)

# # --- Main Page ---
# st.markdown('<h1 class="main-title">🤖 MeitY Knowledge Base AI Agent</h1>', unsafe_allow_html=True)
# st.markdown('<p class="subtitle">Get instant answers about Ministry of Electronics and IT policies, initiatives, and digital governance</p>', unsafe_allow_html=True)

# # Initialize session state
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "latest_query" not in st.session_state:
#     st.session_state.latest_query = ""
# if "latest_response" not in st.session_state:
#     st.session_state.latest_response = None

# # --- Query Input Section ---
# st.markdown("### 💬 Ask Your Question")

# # Sample questions for better UX
# sample_questions = [
#     "What are the key initiatives under Digital India?",
#     "Tell me about MeitY's cybersecurity policies",
#     "What is the National AI Portal about?",
#     "Explain the IT Act amendments",
#     "What are the recent updates in electronics manufacturing policy?"
# ]

# # Quick question buttons
# st.markdown("**Quick Questions:**")
# cols = st.columns(3)
# for i, question in enumerate(sample_questions[:3]):
#     with cols[i]:
#         if st.button(f"📝 {question[:30]}...", key=f"sample_{i}", help=question):
#             st.session_state.sample_question = question

# # Handle sample question selection
# if 'sample_question' in st.session_state:
#     query_text = st.session_state.sample_question
#     del st.session_state.sample_question
# else:
#     query_text = st.text_area(
#         "Enter your question about MeitY, Digital India, or related policies:",
#         height=120,
#         placeholder="Example: What are the main objectives of the National Digital Communications Policy?",
#         help="Ask questions about Ministry of Electronics and IT policies, initiatives, or digital governance topics."
#     )

# # Submit button
# col1, col2, col3 = st.columns([1, 2, 1])
# with col2:
#     submitted = st.button("🔍 Get Answer", type="primary", use_container_width=True)

# # Process query
# if submitted and query_text:
#     st.session_state.latest_query = query_text
#     st.session_state.query_count += 1
    
#     # Show processing status
#     with st.spinner("🔍 Searching knowledge base..."):
#         progress_bar = st.progress(0)
#         status_text = st.empty()
        
#         # Simulate progress updates
#         import time
#         for i, status in enumerate([
#             "Checking local documents...",
#             "Searching web content...", 
#             "Analyzing video transcripts...",
#             "Generating response..."
#         ]):
#             status_text.text(status)
#             progress_bar.progress((i + 1) * 25)
#             if i < 3:
#                 time.sleep(0.5)
        
#         # Get the actual answer
#         try:
#             response = get_answer(query_text)
#             st.session_state.latest_response = response
#             progress_bar.progress(100)
#             status_text.text("✅ Complete!")
            
#             # Log technical details in backend (for monitoring)
#             logger.info(f"Query processed successfully:")
#             logger.info(f"  - Search Method: {response.get('search_method', 'unknown')}")
#             logger.info(f"  - Tier: {response.get('tier', 'unknown')}")
#             logger.info(f"  - Sources Found: {len(response.get('source_documents', []))}")
#             if response.get('similarity_scores'):
#                 scores = response.get('similarity_scores', [])
#                 logger.info(f"  - Score Range: {min(scores):.3f} - {max(scores):.3f}")
            
#             time.sleep(0.5)
#         except Exception as e:
#             logger.error(f"Error processing query: {e}")
#             st.session_state.latest_response = {
#                 "answer": f"An error occurred while processing your query: {str(e)}",
#                 "source_documents": [],
#                 "tier": "Error",
#                 "search_method": "error"
#             }
#         finally:
#             progress_bar.empty()
#             status_text.empty()

# # --- Display Response ---
# if st.session_state.latest_response:
#     st.markdown("---")
    
#     # Query Display
#     st.markdown(f"""
#     <div class="query-display">
#         <strong>🔍 Your Question:</strong> {st.session_state.latest_query}
#     </div>
#     """, unsafe_allow_html=True)
    
#     response_data = st.session_state.latest_response
#     answer_text = response_data.get("answer", "No answer generated.")
    
#     # Display Answer (Clean, no technical details)
#     st.markdown("### 📋 Answer")
#     st.markdown(f"""
#     <div class="answer-container">
#         {answer_text.replace(chr(10), '<br>')}
#     </div>
#     """, unsafe_allow_html=True)

#     # Display Top 5 Sources (Clean display)
#     source_docs = response_data.get("source_documents", [])
    
#     if source_docs:
#         # Always show how many sources we have
#         total_sources = len(source_docs)
#         display_sources = min(5, total_sources)
        
#         st.markdown(f"### 📚 Sources & References ({display_sources} of {total_sources})")
        
#         # Ensure we show up to 5 sources
#         top_sources = source_docs[:5]
        
#         # Display each source with proper indexing
#         for i, doc in enumerate(top_sources):
#             source_info = format_source_display(doc, i)
            
#             # Create expandable source card for better organization
#             with st.expander(f"📋 Source {i + 1}: {source_info['type']} - {source_info['name']}", expanded=True):
#                 st.markdown(f"""
#                 <div class="source-card">
#                     <p><strong>Content Preview:</strong></p>
#                     <p style="font-style: italic; color: #a0a0a0;">{source_info['content_preview']}</p>
#                 </div>
#                 """, unsafe_allow_html=True)
                
#                 # Add download/view options
#                 col1, col2 = st.columns([1, 1])
                
#                 with col1:
#                     # For local files, provide download
#                     if os.path.exists(source_info['full_source']):
#                         try:
#                             with open(source_info['full_source'], "rb") as f:
#                                 file_data = f.read() 
                            
#                             st.download_button(
#                                 label=f"📥 Download Document",
#                                 data=file_data,
#                                 file_name=os.path.basename(source_info['full_source']),
#                                 key=f"download_{i}",
#                                 help=f"Download: {source_info['name']}"
#                             )
#                         except Exception as e:
#                             st.error(f"Unable to load file: {str(e)[:50]}...")
                
#                 with col2:
#                     # For web sources, provide link
#                     if source_info['full_source'].startswith('http'):
#                         st.markdown(f"[🔗 View Online Source]({source_info['full_source']})")
#                     elif not os.path.exists(source_info['full_source']):
#                         st.info("📍 Internal Knowledge Base Reference")
        
#         # Show summary of sources found
#         if total_sources > 5:
#             st.info(f"ℹ️ Showing top 5 most relevant sources. Total {total_sources} sources were found in the knowledge base.")
#         else:
#             st.success(f"All {total_sources} relevant sources are displayed above.")
    
#     else:
#         st.warning("⚠️ No source documents were found or returned. This might indicate an issue with the search system or that the query couldn't be matched to any content in the knowledge base.")
    
#     # Add query to chat history (simplified)
#     st.session_state.chat_history.append({
#         "timestamp": datetime.now(),
#         "query": st.session_state.latest_query,
#         "answer_preview": answer_text[:100] + "..." if len(answer_text) > 100 else answer_text,
#         "source_count": len(source_docs)
#     })

# # --- Chat History ---
# if st.session_state.chat_history:
#     with st.expander("📜 Recent Queries", expanded=False):
#         for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
#             st.markdown(f"""
#             **{entry['timestamp'].strftime('%H:%M:%S')}** - *{entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}*
            
#             *{entry['answer_preview']}*
#             """)
#             st.markdown("---")

# # --- Footer ---
# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; color: #666; padding: 2rem;">
#     <p>🇮🇳 <strong>MeitY Knowledge Base AI Agent</strong></p>
#     <p>Powered by Advanced RAG Technology | Built for Ministry of Electronics and IT</p>
#     <p><em>This system provides information based on official documents, websites, and multimedia content.</em></p>
# </div>
# """, unsafe_allow_html=True)  


# import streamlit as st
# from dotenv import load_dotenv
# import os
# import logging
# from datetime import datetime
# from backend.qa_chain import get_answer

# # Load environment variables
# load_dotenv()

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- Streamlit Page Config ---
# st.set_page_config(
#     page_title="MeitY AI Agent", 
#     layout="wide",
#     initial_sidebar_state="expanded",
#     menu_items={
#         'About': "MeitY Knowledge Base AI Agent - Powered by RAG technology"
#     }
# )

# # --- Custom CSS Styling (no change here) ---
# st.markdown("""
# <style>
#     /* styles omitted for brevity, your original CSS remains unchanged */
# </style>
# """, unsafe_allow_html=True)

# # --- Helper Functions ---
# def format_source_display(doc, index):
#     source = doc.metadata.get('source', 'Unknown Source')
#     title = doc.metadata.get('title', '')
    
#     if source.startswith('http'):
#         source_type = "🌐 Web"
#         display_name = source.split('/')[-1] or source
#         if len(display_name) > 50:
#             display_name = display_name[:47] + "..."
#     elif 'youtube' in source.lower() or 'youtu.be' in source.lower():
#         source_type = "🎬 Video"
#         display_name = title if title else "YouTube Video"
#     else:
#         source_type = "📄 Document"
#         display_name = title if title else os.path.basename(source)
    
#     return {
#         'type': source_type,
#         'name': display_name,
#         'full_source': source,
#         'title': title,
#         'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
#     }

# def find_document_file(source_path):
#     if not source_path:
#         return None
#     if source_path.startswith('http'):
#         return None

#     normalized_path = source_path.replace('\\', '/')
#     filename = os.path.basename(normalized_path)
#     current_dir = os.getcwd()
    
#     logger.info(f"Current working directory: {current_dir}")
#     logger.info(f"Original path: {source_path}")
#     logger.info(f"Normalized path: {normalized_path}")
#     logger.info(f"Looking for file: {filename}")
    
#     persistent_storage_path = os.getenv("PERSISTENT_STORAGE_PATH", "/persistent_storage")

#     possible_paths = [
#         source_path,
#         normalized_path,
#         filename,
#         normalized_path.lstrip('/'),
#         os.path.join("source_documents", filename),
#         os.path.join(".", "source_documents", filename),
#         os.path.join(current_dir, "source_documents", filename),
#         os.path.join(persistent_storage_path, "source_documents", filename),
#         os.path.join(current_dir, persistent_storage_path.strip("/"), "source_documents", filename),
#     ]

    
#     for path in possible_paths:
#         try:
#             if os.path.exists(path) and os.path.isfile(path):
#                 logger.info(f"✅ Found document at: {path}")
#                 return path
#         except Exception:
#             continue

#     logger.warning(f"❌ Could not find document file for: {source_path}")
#     return None

# def try_read_file_content(file_path):
#     encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
#     for encoding in encodings:
#         try:
#             with open(file_path, 'r', encoding=encoding) as f:
#                 return f.read()
#         except UnicodeDecodeError:
#             continue
#         except Exception as e:
#             logger.error(f"Read error with {encoding}: {e}")
#             break
#     try:
#         with open(file_path, 'rb') as f:
#             return f.read()
#     except Exception as e:
#         logger.error(f"Binary read error: {e}")
#         return None


# # --- Enhanced Sidebar ---
# with st.sidebar:
#     st.markdown('''
#     <div class="sidebar-content">
#         <h1 style="color: #ecf0f1; text-align: center; font-weight: 700; margin-bottom: 2rem;">
#             🇮🇳 MeitY AI Agent
#         </h1>
#     </div>
#     ''', unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # About Section
#     st.markdown("""
#     <div class="tech-stack-card">
#         <h3 style="color: #ecf0f1; margin-bottom: 1rem;">📖 About</h3>
#         <p style="color: #bdc3c7; line-height: 1.6;">
#             This AI Agent provides answers using official MeitY documents, 
#             websites, and multimedia content through advanced RAG technology.
#         </p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Tech Stack Section
#     st.markdown("""
#     <div class="tech-stack-card">
#         <h3 style="color: #ecf0f1; margin-bottom: 1rem;">🛠️ Tech Stack</h3>
#         <div style="color: #bdc3c7;">
#             <div style="margin: 0.5rem 0;"><strong>🐍 LLM : </strong>Together AI (Mistral-7B)</div>
#             <div style="margin: 0.5rem 0;"><strong>🎨 Framework : </strong>LangChain</div>
#             <div style="margin: 0.5rem 0;"><strong>🧠 Embeddings : </strong>BAAI BGE-Large</div>
#             <div style="margin: 0.5rem 0;"><strong>💾 Vector DB : </strong>FAISS Vector Embeddings</div>
#             <div style="margin: 0.5rem 0;"><strong>🔍 Search : </strong>Tavily API</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True) 
    
#     # Coverage Areas Section
#     st.markdown("""
#     <div class="coverage-card">
#         <h3 style="color: #ecf0f1; margin-bottom: 1rem;">🎯 Coverage Areas</h3>
#         <div style="color: #bdc3c7;">
#             <div class="coverage-item">🏛️ MeitY Policies & Initiatives</div>
#             <div class="coverage-item">💻 Digital India Programs</div>
#             <div class="coverage-item">🔒 Cybersecurity Guidelines</div>
#             <div class="coverage-item">📱 Technology Standards</div>
#             <div class="coverage-item">🌐 Digital Governance</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # Metrics Section
#     if 'query_count' not in st.session_state:
#         st.session_state.query_count = 0
    
#     st.markdown("""
#     <div class="metric-card">
#         <h3 style="color: #ecf0f1; font-size: 2rem; margin: 0;">""" + str(st.session_state.query_count) + """</h3>
#         <p style="color: #bdc3c7; margin: 0;">Queries Processed</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Additional Info
#     st.markdown("""
#     <div class="tech-stack-card" style="margin-top: 1rem;">
#         <h4 style="color: #ecf0f1;">⚡ Features</h4>
#         <div style="color: #bdc3c7; font-size: 0.9rem;">
#             <div>• Real-time document search</div>
#             <div>• Multi-format support</div>
#             <div>• Source attribution</div>
#             <div>• Download capabilities</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)


# # --- Main Page ---
# st.markdown('<h1 class="main-title">🤖 MeitY Knowledge Base AI Agent</h1>', unsafe_allow_html=True)
# st.markdown('<p class="subtitle">Get instant answers about Ministry of Electronics and IT policies, initiatives, and digital governance</p>', unsafe_allow_html=True)

# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "latest_query" not in st.session_state:
#     st.session_state.latest_query = ""
# if "latest_response" not in st.session_state:
#     st.session_state.latest_response = None

# # --- Query Input Section ---
# st.markdown("### 💬 Ask Your Question")
# query_text = st.text_area(
#     "Enter your question about MeitY, Digital India, or related policies:",
#     height=120,
#     placeholder="Example: What are the main objectives of the National Digital Communications Policy?"
# )
# col1, col2, col3 = st.columns([1, 2, 1])
# with col2:
#     submitted = st.button("🔍 Get Answer", type="primary", use_container_width=True)

# if submitted and query_text:
#     st.session_state.latest_query = query_text
#     st.session_state.query_count += 1
#     with st.spinner("🔍 Searching knowledge base..."):
#         try:
#             response = get_answer(query_text)
#             st.session_state.latest_response = response
#         except Exception as e:
#             st.session_state.latest_response = {
#                 "answer": f"Error occurred: {str(e)}",
#                 "source_documents": []
#             }

# # --- Display Response ---
# if st.session_state.latest_response:
#     st.markdown("---")
#     st.markdown(f"""<div class="query-display"><strong>🔍 Your Question:</strong> {st.session_state.latest_query}</div>""", unsafe_allow_html=True)
    
#     answer_text = st.session_state.latest_response.get("answer", "No answer generated.")
#     st.markdown("### 📋 Answer")
#     st.markdown(f"""<div class="answer-container">{answer_text.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)

#     source_docs = st.session_state.latest_response.get("source_documents", [])
#     if source_docs:
#         st.markdown(f"### 📚 Sources & References ({min(5, len(source_docs))} of {len(source_docs)})")
#         for i, doc in enumerate(source_docs[:5]):
#             source_info = format_source_display(doc, i)
#             with st.expander(f"📋 Source {i + 1}: {source_info['type']} - {source_info['name']}", expanded=True):
#                 st.markdown(f"""<div class="source-card"><p><strong>Content Preview:</strong></p><p style="font-style: italic; color: #a0a0a0;">{source_info['content_preview']}</p></div>""", unsafe_allow_html=True)
#                 col1, col2 = st.columns([1, 1])
#                 with col1:
#                     found_file_path = find_document_file(source_info['full_source'])

#                     if not found_file_path and not source_info['full_source'].startswith('http'):
#                         original_path = source_info['full_source']
#                         normalized_path = original_path.replace('\\', '/')
#                         filename = os.path.basename(normalized_path)
#                         alternative_paths = [
#                             original_path,
#                             normalized_path,
#                             filename,
#                             os.path.join("source_documents", filename),
#                             os.path.join(".", "source_documents", filename),
#                             os.path.join(os.getcwd(), "source_documents", filename),
#                         ]
#                         for alt_path in alternative_paths:
#                             if os.path.exists(alt_path) and os.path.isfile(alt_path):
#                                 found_file_path = alt_path
#                                 break

#                     if found_file_path:
#                         file_content = try_read_file_content(found_file_path)
#                         if file_content:
#                             file_data = file_content.encode('utf-8') if isinstance(file_content, str) else file_content
#                             st.download_button(
#                                 label=f"📥 Download Document",
#                                 data=file_data,
#                                 file_name=os.path.basename(found_file_path),
#                                 key=f"download_{i}",
#                                 help=f"Download: {source_info['name']}"
#                             )
#                     else:
#                         if source_info['full_source'].startswith('http'):
#                             st.info("🌐 Web source - see link below")
#                         else:
#                             st.warning("📍 File not accessible for download")
#                             with st.expander("🔧 Debug Info", expanded=False):
#                                 normalized_path = source_info['full_source'].replace('\\', '/')
#                                 filename = os.path.basename(source_info['full_source'])
#                                 st.write("**Original path:**", source_info['full_source'])
#                                 st.write("**Normalized path:**", normalized_path)
#                                 st.write("**Filename:**", filename)
#                                 st.write("**Current directory:**", os.getcwd())

#                 with col2:
#                     if source_info['full_source'].startswith('http'):
#                         st.markdown(f"[🔗 View Online Source]({source_info['full_source']})")
#                     else:
#                         st.code(f"Source: {source_info['full_source']}")

# # --- Footer ---
# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; color: #666; padding: 2rem;">
#     <p>🇮🇳 <strong>MeitY Knowledge Base AI Agent</strong></p>
#     <p>Powered by Advanced RAG Technology | Built for Ministry of Electronics and IT</p>
# </div>
# """, unsafe_allow_html=True)

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

# --- Custom CSS Styling (no change here) ---
st.markdown("""
<style>
    /* styles omitted for brevity, your original CSS remains unchanged */
    .example-question-btn {
        background-color: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 5px;
        color: #ecf0f1;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 14px;
        width: 100%;
        display: block;
    }
    .example-question-btn:hover {
        background-color: #34495e;
        border-color: #3498db;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_source_display(doc, index):
    source = doc.metadata.get('source', 'Unknown Source')
    title = doc.metadata.get('title', '')
    
    if source.startswith('http'):
        source_type = "🌐 Web"
        display_name = source.split('/')[-1] or source
        if len(display_name) > 50:
            display_name = display_name[:47] + "..."
    elif 'youtube' in source.lower() or 'youtu.be' in source.lower():
        source_type = "🎬 Video"
        display_name = title if title else "YouTube Video"
    else:
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
    if not source_path:
        return None
    if source_path.startswith('http'):
        return None

    normalized_path = source_path.replace('\\', '/')
    filename = os.path.basename(normalized_path)
    current_dir = os.getcwd()
    
    logger.info(f"Current working directory: {current_dir}")
    logger.info(f"Original path: {source_path}")
    logger.info(f"Normalized path: {normalized_path}")
    logger.info(f"Looking for file: {filename}")
    
    persistent_storage_path = os.getenv("PERSISTENT_STORAGE_PATH", "/persistent_storage")

    possible_paths = [
        source_path,
        normalized_path,
        filename,
        normalized_path.lstrip('/'),
        os.path.join("source_documents", filename),
        os.path.join(".", "source_documents", filename),
        os.path.join(current_dir, "source_documents", filename),
        os.path.join(persistent_storage_path, "source_documents", filename),
        os.path.join(current_dir, persistent_storage_path.strip("/"), "source_documents", filename),
    ]

    
    for path in possible_paths:
        try:
            if os.path.exists(path) and os.path.isfile(path):
                logger.info(f"✅ Found document at: {path}")
                return path
        except Exception:
            continue

    logger.warning(f"❌ Could not find document file for: {source_path}")
    return None

def try_read_file_content(file_path):
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Read error with {encoding}: {e}")
            break
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Binary read error: {e}")
        return None

def process_question(question):
    """Process the selected question and get answer"""
    st.session_state.latest_query = question
    st.session_state.query_count += 1
    with st.spinner("🔍 Searching knowledge base..."):
        try:
            response = get_answer(question)
            st.session_state.latest_response = response
        except Exception as e:
            st.session_state.latest_response = {
                "answer": f"Error occurred: {str(e)}",
                "source_documents": []
            }

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown('''
    <div class="sidebar-content">
        <h1 style="color: #ecf0f1; text-align: center; font-weight: 700; margin-bottom: 2rem;">
            🇮🇳 MeitY AI Agent
        </h1>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # About Section
    st.markdown("""
    <div class="tech-stack-card">
        <h3 style="color: #ecf0f1; margin-bottom: 1rem;">📖 About</h3>
        <p style="color: #bdc3c7; line-height: 1.6;">
            This AI Agent provides answers using official MeitY documents, 
            websites, and multimedia content through advanced RAG technology.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tech Stack Section
    st.markdown("""
    <div class="tech-stack-card">
        <h3 style="color: #ecf0f1; margin-bottom: 1rem;">🛠️ Tech Stack</h3>
        <div style="color: #bdc3c7;">
            <div style="margin: 0.5rem 0;"><strong>🐍 LLM : </strong>Together AI (Mistral-7B)</div>
            <div style="margin: 0.5rem 0;"><strong>🎨 Framework : </strong>LangChain</div>
            <div style="margin: 0.5rem 0;"><strong>🧠 Embeddings : </strong>BAAI BGE-Large</div>
            <div style="margin: 0.5rem 0;"><strong>💾 Vector DB : </strong>FAISS Vector Embeddings</div>
            <div style="margin: 0.5rem 0;"><strong>🔍 Search : </strong>Tavily API</div>
        </div>
    </div>
    """, unsafe_allow_html=True) 
    
    # Coverage Areas Section
    st.markdown("""
    <div class="coverage-card">
        <h3 style="color: #ecf0f1; margin-bottom: 1rem;">🎯 Coverage Areas</h3>
        <div style="color: #bdc3c7;">
            <div class="coverage-item">🏛️ MeitY Policies & Initiatives</div>
            <div class="coverage-item">💻 Digital India Programs</div>
            <div class="coverage-item">🔒 Cybersecurity Guidelines</div>
            <div class="coverage-item">📱 Technology Standards</div>
            <div class="coverage-item">🌐 Digital Governance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Metrics Section
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    st.markdown("""
    <div class="metric-card">
        <h3 style="color: #ecf0f1; font-size: 2rem; margin: 0;">""" + str(st.session_state.query_count) + """</h3>
        <p style="color: #bdc3c7; margin: 0;">Queries Processed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Additional Info
    st.markdown("""
    <div class="tech-stack-card" style="margin-top: 1rem;">
        <h4 style="color: #ecf0f1;">⚡ Features</h4>
        <div style="color: #bdc3c7; font-size: 0.9rem;">
            <div>• Real-time document search</div>
            <div>• Multi-format support</div>
            <div>• Source attribution</div>
            <div>• Download capabilities</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- Main Page ---
st.markdown('<h1 class="main-title">🤖 MeitY Knowledge Base AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get instant answers about Ministry of Electronics and IT policies, initiatives, and digital governance</p>', unsafe_allow_html=True)

# Initialize session states
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "latest_query" not in st.session_state:
    st.session_state.latest_query = ""
if "latest_response" not in st.session_state:
    st.session_state.latest_response = None

# Example questions
example_questions = [
    "What are the main objectives of the National Digital Communications Policy?",
    "How does Digital India initiative promote digital literacy?",
    "What are the cybersecurity guidelines for government organizations?",
    "Explain the IT Act 2000 and its amendments",
    "What is the role of MeitY in promoting startups?"
]

# --- Example Questions Section ---
st.markdown("### 💡 Try These Example Questions")
st.markdown("Click on any question below to get instant answers:")

# Display example questions in a grid layout
cols = st.columns(2)
for i, question in enumerate(example_questions):
    with cols[i % 2]:
        if st.button(
            question,
            key=f"example_q_{i}",
            help=f"Click to ask: {question}",
            use_container_width=True
        ):
            process_question(question)
            st.rerun()

st.markdown("---")

# --- Query Input Section ---
st.markdown("### 💬 Ask Your Own Question")
query_text = st.text_area(
    "Enter your question about MeitY, Digital India, or related policies:",
    height=120,
    placeholder="Example: What are the main objectives of the National Digital Communications Policy?"
)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submitted = st.button("🔍 Get Answer", type="primary", use_container_width=True)

if submitted and query_text:
    process_question(query_text)

# --- Display Response ---
if st.session_state.latest_response:
    st.markdown("---")
    st.markdown(f"""<div class="query-display"><strong>🔍 Your Question:</strong> {st.session_state.latest_query}</div>""", unsafe_allow_html=True)
    
    answer_text = st.session_state.latest_response.get("answer", "No answer generated.")
    st.markdown("### 📋 Answer")
    st.markdown(f"""<div class="answer-container">{answer_text.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)

    source_docs = st.session_state.latest_response.get("source_documents", [])
    if source_docs:
        st.markdown(f"### 📚 Sources & References ({min(5, len(source_docs))} of {len(source_docs)})")
        for i, doc in enumerate(source_docs[:5]):
            source_info = format_source_display(doc, i)
            with st.expander(f"📋 Source {i + 1}: {source_info['type']} - {source_info['name']}", expanded=True):
                st.markdown(f"""<div class="source-card"><p><strong>Content Preview:</strong></p><p style="font-style: italic; color: #a0a0a0;">{source_info['content_preview']}</p></div>""", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                with col1:
                    found_file_path = find_document_file(source_info['full_source'])

                    if not found_file_path and not source_info['full_source'].startswith('http'):
                        original_path = source_info['full_source']
                        normalized_path = original_path.replace('\\', '/')
                        filename = os.path.basename(normalized_path)
                        alternative_paths = [
                            original_path,
                            normalized_path,
                            filename,
                            os.path.join("source_documents", filename),
                            os.path.join(".", "source_documents", filename),
                            os.path.join(os.getcwd(), "source_documents", filename),
                        ]
                        for alt_path in alternative_paths:
                            if os.path.exists(alt_path) and os.path.isfile(alt_path):
                                found_file_path = alt_path
                                break

                    if found_file_path:
                        file_content = try_read_file_content(found_file_path)
                        if file_content:
                            file_data = file_content.encode('utf-8') if isinstance(file_content, str) else file_content
                            st.download_button(
                                label=f"📥 Download Document",
                                data=file_data,
                                file_name=os.path.basename(found_file_path),
                                key=f"download_{i}",
                                help=f"Download: {source_info['name']}"
                            )
                    else:
                        if source_info['full_source'].startswith('http'):
                            st.info("🌐 Web source - see link below")
                        else:
                            st.warning("📍 File not accessible for download")
                            with st.expander("🔧 Debug Info", expanded=False):
                                normalized_path = source_info['full_source'].replace('\\', '/')
                                filename = os.path.basename(source_info['full_source'])
                                st.write("**Original path:**", source_info['full_source'])
                                st.write("**Normalized path:**", normalized_path)
                                st.write("**Filename:**", filename)
                                st.write("**Current directory:**", os.getcwd())

                with col2:
                    if source_info['full_source'].startswith('http'):
                        st.markdown(f"[🔗 View Online Source]({source_info['full_source']})")
                    else:
                        st.code(f"Source: {source_info['full_source']}")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🇮🇳 <strong>MeitY Knowledge Base AI Agent</strong></p>
    <p>Powered by Advanced RAG Technology | Built for Ministry of Electronics and IT</p>
</div>
""", unsafe_allow_html=True)