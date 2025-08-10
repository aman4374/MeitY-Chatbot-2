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
from langchain.docstore.document import Document

# --- Paths to the pre-built FAISS indexes ---
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")


def search_vectorstore(index_path, query, embeddings):
    """Loads a FAISS index and returns a list of source documents."""
    max_retries = 3
    retry_delay = 2 # seconds
    for attempt in range(max_retries):
        if os.path.exists(index_path) and os.path.exists(os.path.join(index_path, "index.faiss")):
            break
        else:
            print(f"Path or index file in '{index_path}' not found. Attempt {attempt + 1}/{max_retries}. Retrying...")
            time.sleep(retry_delay)
    else:
        print(f"CRITICAL: Path '{index_path}' not found after {max_retries} retries.")
        return []

    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    results = vectordb.similarity_search_with_relevance_scores(query, k=5)
    
    threshold = 0.75 # Adjusted for potentially better relevance
    relevant_docs = [doc for doc, score in results if score > threshold]
    return relevant_docs


def ask_llm(query: str, context_docs: list[Document]) -> dict:
    """
    Generates an answer from the LLM based on context documents.
    Returns a dictionary with the answer and the source documents.
    """
    context = "\n\n".join([doc.page_content for doc in context_docs])
    
    prompt = f"""You are an expert assistant. Use only the provided context to provide a detailed and comprehensive answer.

Context:
{context}

Question: {query}
Answer:"""

    llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3)
    response = llm.invoke(prompt)
    answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

    # Check for failure phrases
    failure_phrases = [
        "i do not have enough information",
        "the provided context does not",
    ]
    is_failure = any(phrase in answer_text.lower() for phrase in failure_phrases)

    # Return None for answer if it was a failure, so the next tier can be checked
    if is_failure:
        return None

    return {
        "answer": answer_text,
        "source_documents": context_docs
    }


def get_answer(query: str) -> dict:
    """
    Answers a query using tiered search and returns a dictionary
    containing the answer and a list of source documents.
    """
    embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    
    # Tier 1: Local Documents
    print("Checking 📄 Documents...")
    doc_sources = search_vectorstore(DOC_FAISS_PATH, query, embeddings)
    if doc_sources:
        result = ask_llm(query, doc_sources)
        if result:
            return result

    # Tier 2: Scraped Websites
    print("Checking 🌐 Scraped Websites...")
    scraped_sources = search_vectorstore(SCRAPED_FAISS_PATH, query, embeddings)
    if scraped_sources:
        result = ask_llm(query, scraped_sources)
        if result:
            return result
            
    # Tier 3: YouTube Transcripts
    print("Checking 🎬 YouTube Videos...")
    youtube_sources = search_vectorstore(YOUTUBE_FAISS_PATH, query, embeddings)
    if youtube_sources:
        result = ask_llm(query, youtube_sources)
        if result:
            return result

    # Tier 4: Fallback to Internet Search
    try:
        print("🔍 No relevant info found. Falling back to Internet...")
        web_results = search_tavily(query)
        if web_results:
            web_docs = [Document(page_content=res['content'], metadata={'source': res['url']}) for res in web_results]
            return ask_llm(query, web_docs)
        else:
            return {"answer": "Could not find a relevant answer from the knowledge base or the internet.", "source_documents": []}
    except Exception as e:
        return {"answer": f"An error occurred during internet fallback: {e}", "source_documents": []}