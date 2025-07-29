import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_together import ChatTogether
from langchain_core.messages import AIMessage
from backend.web_search import search_tavily

# --- MODIFIED: Correctly determine paths for both local and cloud environments ---
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")


def search_vectorstore(index_path, query, embeddings):
    """Loads a FAISS index and searches for relevant documents."""
    if not os.path.exists(index_path):
        print(f"Warning: Index path does not exist: {index_path}")
        return None
    
    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    results = vectordb.similarity_search_with_score(query, k=4)
    threshold = 1.2
    relevant_docs = [doc for doc, score in results if score < threshold]
    return relevant_docs if relevant_docs else None


def ask_llm(query: str, context: str, source: str) -> tuple[bool, str]:
    """
    Sends the query to the LLM and analyzes the response.
    Returns a tuple: (was_answer_found, formatted_response_string)
    """
    prompt = f"""You are an expert assistant. Use only the provided context to answer the question concisely. If the context does not contain the answer, you must say "I do not have enough information to answer that."

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
    
    formatted_response = f"{source}:\n{answer_text}"
    
    return not is_failure, formatted_response


def get_answer(query: str) -> str:
    """Answers a query using an intelligent tiered search."""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Tier 1: Local Documents (Golden Data)
    try:
        print("Checking 📄 Documents...")
        docs = search_vectorstore(DOC_FAISS_PATH, query, embeddings)
        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])
            success, answer = ask_llm(query, context, source="📄 Answer (from documents)")
            if success:
                return answer
    except Exception as e:
        print(f"Error searching documents: {e}")

    # Tier 2: Scraped Websites
    try:
        print("Checking 🌐 Scraped Websites...")
        docs = search_vectorstore(SCRAPED_FAISS_PATH, query, embeddings)
        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])
            success, answer = ask_llm(query, context, source="🌐 Answer (from scraped websites)")
            if success:
                return answer
    except Exception as e:
        print(f"Error searching scraped websites: {e}")

    # Tier 3: YouTube Transcripts
    try:
        print("Checking 🎬 YouTube Videos...")
        docs = search_vectorstore(YOUTUBE_FAISS_PATH, query, embeddings)
        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])
            success, answer = ask_llm(query, context, source="🎬 Answer (from YouTube videos)")
            if success:
                return answer
    except Exception as e:
        print(f"Error searching YouTube videos: {e}")

    # Tier 4: Tavily Internet Search (Final Fallback)
    try:
        print("🔍 No relevant info found in any local source. Falling back to Internet...")
        tavily_answer = search_tavily(query)
        return f"🌐 **Answer (via Internet):**\n{tavily_answer}"
    except Exception as e:
        return f"❌ Internet fallback failed: {e}"