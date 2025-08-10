# backend/qa_chain.py
# import os
# import time
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import SentenceTransformerEmbeddings
# from langchain_together import ChatTogether
# from langchain_core.messages import AIMessage
# from backend.web_search import search_tavily
# from langchain.docstore.document import Document

# # --- Paths to the pre-built FAISS indexes ---
# PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
# DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
# SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
# YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")


# def search_vectorstore(index_path, query, embeddings):
#     """Loads a FAISS index and returns a list of source documents."""
#     max_retries = 3
#     retry_delay = 2 # seconds
#     for attempt in range(max_retries):
#         if os.path.exists(index_path) and os.path.exists(os.path.join(index_path, "index.faiss")):
#             break
#         else:
#             print(f"Path or index file in '{index_path}' not found. Attempt {attempt + 1}/{max_retries}. Retrying...")
#             time.sleep(retry_delay)
#     else:
#         print(f"CRITICAL: Path '{index_path}' not found after {max_retries} retries.")
#         return []

#     vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
#     results = vectordb.similarity_search_with_relevance_scores(query, k=5)
    
#     threshold = 0.75 # Adjusted for potentially better relevance
#     relevant_docs = [doc for doc, score in results if score > threshold]
#     return relevant_docs


# def ask_llm(query: str, context_docs: list[Document]) -> dict:
#     """
#     Generates an answer from the LLM based on context documents.
#     Returns a dictionary with the answer and the source documents.
#     """
#     context = "\n\n".join([doc.page_content for doc in context_docs])
    
#     prompt = f"""You are an expert assistant. Use only the provided context to provide a detailed and comprehensive answer.

# Context:
# {context}

# Question: {query}
# Answer:"""

#     llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3)
#     response = llm.invoke(prompt)
#     answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

#     # Check for failure phrases
#     failure_phrases = [
#         "i do not have enough information",
#         "the provided context does not",
#     ]
#     is_failure = any(phrase in answer_text.lower() for phrase in failure_phrases)

#     # Return None for answer if it was a failure, so the next tier can be checked
#     if is_failure:
#         return None

#     return {
#         "answer": answer_text,
#         "source_documents": context_docs
#     }


# def get_answer(query: str) -> dict:
#     """
#     Answers a query using tiered search and returns a dictionary
#     containing the answer and a list of source documents.
#     """
#     embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    
#     # Tier 1: Local Documents
#     print("Checking 📄 Documents...")
#     doc_sources = search_vectorstore(DOC_FAISS_PATH, query, embeddings)
#     if doc_sources:
#         result = ask_llm(query, doc_sources)
#         if result:
#             return result

#     # Tier 2: Scraped Websites
#     print("Checking 🌐 Scraped Websites...")
#     scraped_sources = search_vectorstore(SCRAPED_FAISS_PATH, query, embeddings)
#     if scraped_sources:
#         result = ask_llm(query, scraped_sources)
#         if result:
#             return result
            
#     # Tier 3: YouTube Transcripts
#     print("Checking 🎬 YouTube Videos...")
#     youtube_sources = search_vectorstore(YOUTUBE_FAISS_PATH, query, embeddings)
#     if youtube_sources:
#         result = ask_llm(query, youtube_sources)
#         if result:
#             return result

#     # Tier 4: Fallback to Internet Search
#     try:
#         print("🔍 No relevant info found. Falling back to Internet...")
#         web_results = search_tavily(query)
#         if web_results:
#             web_docs = [Document(page_content=res['content'], metadata={'source': res['url']}) for res in web_results]
#             return ask_llm(query, web_docs)
#         else:
#             return {"answer": "Could not find a relevant answer from the knowledge base or the internet.", "source_documents": []}
#     except Exception as e:
#         return {"answer": f"An error occurred during internet fallback: {e}", "source_documents": []}  


import os
import time
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_together import ChatTogether
from langchain_core.messages import AIMessage
from backend.web_search import search_tavily
from langchain.docstore.document import Document

# --- FAISS Index Paths ---
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")

# --- Embedding Model ---
embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")


def search_vectorstore(index_path, query, threshold=0.75, k=5):
    """Load FAISS index and return relevant documents."""
    if not os.path.exists(index_path) or not os.path.exists(os.path.join(index_path, "index.faiss")):
        return []

    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    results = vectordb.similarity_search_with_relevance_scores(query, k=k)

    return [(doc, score) for doc, score in results if score > threshold]


def ask_llm(query, context_docs):
    """Call Together AI with given context."""
    context = "\n\n".join([doc.page_content for doc in context_docs])
    prompt = f"""You are a knowledgeable assistant. Use the following context to answer the question strictly from it.

Context:
{context}

Question: {query}
Answer:"""

    llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.3)
    response = llm.invoke(prompt)
    answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

    # Detect failure responses
    if any(x in answer_text.lower() for x in [
        "i do not have enough information", 
        "the provided context does not", 
        "i'm not sure"
    ]):
        return None
    return {"answer": answer_text, "source_documents": context_docs}


def get_answer(query):
    """Returns a response and references using tiered fallback."""
    # --- 1. Local Docs ---
    print("🔍 Checking 📄 Local Documents...")
    doc_results = search_vectorstore(DOC_FAISS_PATH, query)
    if doc_results:
        top_docs = [doc for doc, _ in doc_results]
        result = ask_llm(query, top_docs)
        if result:
            return result

    # --- 2. Scraped Websites ---
    print("🔍 Checking 🌐 Scraped Websites...")
    scraped_results = search_vectorstore(SCRAPED_FAISS_PATH, query)
    if scraped_results:
        top_docs = [doc for doc, _ in scraped_results]
        result = ask_llm(query, top_docs)
        if result:
            return result

    # --- 3. YouTube Transcripts ---
    print("🔍 Checking 🎬 YouTube Videos...")
    youtube_results = search_vectorstore(YOUTUBE_FAISS_PATH, query)
    if youtube_results:
        top_docs = [doc for doc, _ in youtube_results]
        result = ask_llm(query, top_docs)
        if result:
            return result

    # --- 4. Fallback: Internet Search ---
    print("🌐 Falling back to Tavily...")
    try:
        web_results = search_tavily(query)
        if web_results:
            web_docs = [Document(page_content=res['content'], metadata={'source': res['url']}) for res in web_results]
            return ask_llm(query, web_docs)
    except Exception as e:
        return {"answer": f"Internet search failed: {e}", "source_documents": []}

    return {"answer": "No relevant information was found.", "source_documents": []}
