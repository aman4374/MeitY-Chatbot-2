# import os
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import SentenceTransformerEmbeddings
# from langchain_together import ChatTogether
# from langchain_core.messages import AIMessage
# from backend.web_search import search_tavily

# # --- Paths to the pre-built FAISS indexes ---
# PERSISTENT_DIR = "persistent_storage"
# DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
# SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
# YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")

# def search_vectorstore(index_path, query, embeddings):
#     """Loads a FAISS index and searches for relevant documents."""
#     if not os.path.exists(index_path):
#         return None
    
#     vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
#     results = vectordb.similarity_search_with_score(query, k=4)
#     threshold = 1.2
#     relevant_docs = [doc for doc, score in results if score < threshold]
#     return relevant_docs if relevant_docs else None

# # --- MODIFIED: ask_llm now returns a success flag ---
# def ask_llm(query: str, context: str, source: str) -> tuple[bool, str]:
#     """
#     Sends the query to the LLM and analyzes the response.
#     Returns a tuple: (was_answer_found, formatted_response_string)
#     """
#     prompt = f"""You are an expert assistant. Use only the provided context to answer the question concisely. If the context does not contain the answer, you must say "I do not have enough information to answer that."

# Context:
# {context}

# Question: {query}
# Answer:"""

#     llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.2)
#     response = llm.invoke(prompt)
#     answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

#     # --- NEW: Check if the LLM admitted it couldn't answer ---
#     failure_phrases = [
#         "i do not have enough information",
#         "i don't have enough information",
#         "the context does not contain"
#     ]
    
#     # Check if any failure phrase is in the lowercase version of the answer
#     is_failure = any(phrase in answer_text.lower() for phrase in failure_phrases)
    
#     formatted_response = f"{source}:\n{answer_text}"
    
#     # If it was a failure, return False. Otherwise, return True.
#     return not is_failure, formatted_response


# # --- MODIFIED: get_answer now uses the success flag for fallback ---
# def get_answer(query: str) -> str:
#     """Answers a query using an intelligent tiered search."""
#     embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
#     # Tier 1: Local Documents (Golden Data)
#     print("Checking 📄 Documents...")
#     docs = search_vectorstore(DOC_FAISS_PATH, query, embeddings)
#     if docs:
#         context = "\n\n".join([doc.page_content for doc in docs])
#         success, answer = ask_llm(query, context, source="📄 Answer (from documents)")
#         if success:
#             return answer

#     # Tier 2: Scraped Websites
#     print("Checking 🌐 Scraped Websites...")
#     docs = search_vectorstore(SCRAPED_FAISS_PATH, query, embeddings)
#     if docs:
#         context = "\n\n".join([doc.page_content for doc in docs])
#         success, answer = ask_llm(query, context, source="🌐 Answer (from scraped websites)")
#         if success:
#             return answer

#     # Tier 3: YouTube Transcripts
#     print("Checking 🎬 YouTube Videos...")
#     docs = search_vectorstore(YOUTUBE_FAISS_PATH, query, embeddings)
#     if docs:
#         context = "\n\n".join([doc.page_content for doc in docs])
#         success, answer = ask_llm(query, context, source="🎬 Answer (from YouTube videos)")
#         if success:
#             return answer

#     # Tier 4: Tavily Internet Search (Final Fallback)
#     try:
#         print("🔍 No relevant info found in any local source. Falling back to Internet...")
#         tavily_answer = search_tavily(query)
#         return f"🌐 **Answer (via Internet):**\n{tavily_answer}"
#     except Exception as e:
#         return f"❌ Internet fallback failed: {e}"



import os
import time
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_together import ChatTogether
from langchain_core.messages import AIMessage
from backend.web_search import search_tavily

# --- Paths to the pre-built FAISS indexes ---
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")

def search_vectorstore(index_path, query, embeddings):
    """Loads a FAISS index and searches for relevant documents with retry logic."""
    max_retries = 3
    retry_delay = 2 # seconds
    for attempt in range(max_retries):
        if os.path.exists(index_path):
            break
        else:
            print(f"Path '{index_path}' not found. Attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
    else:
        print(f"CRITICAL: Path '{index_path}' not found after {max_retries} retries.")
        return None
    
    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    results = vectordb.similarity_search_with_score(query, k=4)
    threshold = 1.2
    relevant_docs = [doc for doc, score in results if score < threshold]
    return relevant_docs if relevant_docs else None

# --- MODIFIED: ask_llm now returns the raw text ---
def ask_llm(query: str, context: str) -> tuple[bool, str]:
    """
    Sends the query to the LLM and analyzes the response.
    Returns a tuple: (was_answer_found, raw_answer_text)
    """
    prompt = f"""You are an expert assistant. Use only the provided context to answer the question concisely. If the context contains URLs, you must cite them at the end of your answer. If the context does not contain the answer, you must say "I do not have enough information to answer that."

Context:
{context}

Question: {query}
Answer:"""

    llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.2)
    response = llm.invoke(prompt)
    answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

    failure_phrases = [
        "i do not have enough information",
        "i don't have enough information",
        "the context does not contain"
    ]
    
    is_failure = any(phrase in answer_text.lower() for phrase in failure_phrases)
    
    # Return the success flag and the raw answer text
    return not is_failure, answer_text

# --- MODIFIED: get_answer now handles all response formatting ---
def get_answer(query: str) -> str:
    """Answers a query using an intelligent tiered search."""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    source_answer_map = {
        DOC_FAISS_PATH: "📄 Answer (from documents)",
        SCRAPED_FAISS_PATH: "🌐 Answer (from scraped websites)",
        YOUTUBE_FAISS_PATH: "🎬 Answer (from YouTube videos)"
    }

    for index_path, source_text in source_answer_map.items():
        print(f"Checking {source_text}...")
        docs = search_vectorstore(index_path, query, embeddings)
        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])
            success, answer_text = ask_llm(query, context)
            if success:
                # Format the successful response here
                return f"{source_text}:\n{answer_text}"

    # Fallback to Internet Search
    try:
        print("🔍 No relevant info found in any local source. Falling back to Internet...")
        web_results = search_tavily(query)
        if web_results:
            web_context = "\n\n".join([f"Source: {res['url']}\nContent: {res['content']}" for res in web_results])
            # We don't need the 'success' flag here as it's the final step
            _, answer_text = ask_llm(query, web_context)
            return f"🌐 Answer (via Internet):\n{answer_text}"
        else:
            return "❌ Could not find an answer from the internet."
    except Exception as e:
        return f"❌ Internet fallback failed: {e}"