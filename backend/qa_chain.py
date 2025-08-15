import os
import time
import logging
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_together import ChatTogether
from langchain_core.messages import AIMessage
from backend.web_search import search_tavily
from langchain.docstore.document import Document

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Paths to the pre-built FAISS indexes ---
PERSISTENT_DIR = os.environ.get("PERSISTENT_STORAGE_PATH", "persistent_storage")
DOC_FAISS_PATH = os.path.join(PERSISTENT_DIR, "doc_faiss_index")
SCRAPED_FAISS_PATH = os.path.join(PERSISTENT_DIR, "scraped_faiss_index")
YOUTUBE_FAISS_PATH = os.path.join(PERSISTENT_DIR, "youtube_faiss_index")

# --- Embedding Model (Load Once) ---
try:
    embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    logger.info("✅ Embeddings model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load embeddings model: {e}")
    raise

# --- Enhanced Configuration ---
class SearchConfig:
    DEFAULT_THRESHOLD = 0.7  # Slightly lowered for better recall
    RELAXED_THRESHOLD = 0.5  # More relaxed for fallback
    EMERGENCY_THRESHOLD = 0.3  # Emergency fallback threshold
    MAX_DOCS_PER_TIER = 8  # Increased for better context
    MAX_TOTAL_DOCS = 20  # Increased for combined search
    TEMPERATURE = 0.3  # Lower temperature for more focused answers
    MAX_RETRIES = 3
    
    # Enhanced failure detection phrases
    FAILURE_PHRASES = [
        "i do not have enough information",
        "the provided context does not",
        "the context does not contain",
        "i'm not sure",
        "i don't know",
        "cannot find",
        "no information",
        "insufficient information",
        "unclear from the context",
        "not mentioned in the context",
        "based on the context provided, i cannot",
        "the context doesn't provide",
        "i cannot determine",
        "there is no mention"
    ]


def search_vectorstore(index_path: str, query: str, threshold: float = SearchConfig.DEFAULT_THRESHOLD) -> List[Document]:
    """Loads a FAISS index and returns relevant documents with retry mechanism."""
    for attempt in range(SearchConfig.MAX_RETRIES):
        try:
            if not os.path.exists(index_path):
                logger.warning(f"Index directory not found: {index_path}")
                return []
                
            faiss_file = os.path.join(index_path, "index.faiss")
            if not os.path.exists(faiss_file):
                logger.warning(f"FAISS index file not found: {faiss_file}")
                return []

            vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            results = vectordb.similarity_search_with_relevance_scores(query, k=SearchConfig.MAX_DOCS_PER_TIER)
            
            relevant_docs = [doc for doc, score in results if score > threshold]
            logger.info(f"Found {len(relevant_docs)}/{len(results)} relevant docs in {os.path.basename(index_path)} (threshold: {threshold})")
            
            # Log top scores for debugging
            if results:
                top_scores = [score for _, score in results[:3]]
                logger.debug(f"Top similarity scores: {top_scores}")
            
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {index_path}: {e}")
            if attempt < SearchConfig.MAX_RETRIES - 1:
                time.sleep(1)  # Brief pause before retry
            else:
                logger.error(f"All attempts failed for vectorstore search in {index_path}")
                return []
    
    return []


def is_answer_failure(answer_text: str) -> bool:
    """Enhanced failure detection with more comprehensive checks."""
    if not answer_text or not answer_text.strip():
        return True
        
    answer_lower = answer_text.lower().strip()
    
    # Check for failure phrases
    for phrase in SearchConfig.FAILURE_PHRASES:
        if phrase in answer_lower:
            logger.debug(f"Failure phrase detected: '{phrase}'")
            return True
    
    # Check for very short answers (likely incomplete)
    if len(answer_text.strip()) < 15:
        logger.debug(f"Answer too short: {len(answer_text.strip())} characters")
        return True
        
    # Check for answers that are just questions or non-informative
    if answer_text.strip().endswith('?') and len(answer_text.split()) < 20:
        logger.debug("Answer appears to be a question")
        return True
    
    # Check for generic non-answers
    generic_responses = ["sorry", "apologize", "unable to help", "try again"]
    if any(generic in answer_lower for generic in generic_responses) and len(answer_text.split()) < 30:
        logger.debug("Generic non-answer detected")
        return True
        
    return False


def ask_llm(query: str, context_docs: List[Document], attempt_type: str = "standard") -> Optional[Dict]:
    """Enhanced LLM querying with better prompting and failure detection."""
    if not context_docs:
        logger.warning("No context documents provided to LLM")
        return None
        
    # Limit total context to avoid overwhelming the LLM
    if len(context_docs) > SearchConfig.MAX_TOTAL_DOCS:
        context_docs = context_docs[:SearchConfig.MAX_TOTAL_DOCS]
        logger.info(f"Truncated context to {SearchConfig.MAX_TOTAL_DOCS} documents")
        
    # Build context with better formatting
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc.metadata.get('source', 'Unknown Source')
        title = doc.metadata.get('title', '')
        
        # Format source nicely
        if source.startswith('http'):
            source_display = f"Web: {source}"
        elif os.path.exists(source):
            source_display = f"Document: {os.path.basename(source)}"
        else:
            source_display = f"Source: {source}"
        
        if title:
            source_display += f" ({title})"
            
        context_parts.append(f"[Source {i}] {source_display}\n{doc.page_content.strip()}")
    
    context = "\n\n".join(context_parts)
    
    # Enhanced prompts based on attempt type
    if attempt_type == "web_fallback":
        prompt = f"""You are a knowledgeable assistant helping with questions about MeitY (Ministry of Electronics and IT, India). I found some information from the internet that should help answer the user's question.

Web Search Results:
{context}

Question: {query}

Please provide a comprehensive and accurate answer based on the search results above. Focus on MeitY-related information and be specific. If the information seems insufficient or unclear, please state what additional information would be helpful."""

    elif attempt_type == "combined_relaxed":
        prompt = f"""You are a knowledgeable assistant specializing in MeitY (Ministry of Electronics and IT, India) topics. I'm providing you with information from multiple sources (documents, websites, videos) that might help answer the user's question.

Combined Sources:
{context}

Question: {query}

Please synthesize the information from all sources to provide a comprehensive answer. Focus on the most relevant and authoritative information. If sources conflict, mention the discrepancy. If information is incomplete, state what's missing."""

    else:  # standard
        prompt = f"""You are an expert assistant specializing in MeitY (Ministry of Electronics and IT, India) and related technology policy topics. Use the provided context to give a detailed, accurate answer.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based strictly on the provided context. Be specific and cite relevant details from the sources. If the context doesn't contain enough information to fully answer the question, clearly state what information is missing or unclear."""

    try:
        llm = ChatTogether(
            model="mistralai/Mistral-7B-Instruct-v0.2", 
            temperature=SearchConfig.TEMPERATURE,
            max_tokens=1000  # Ensure we get complete responses
        )
        
        logger.info(f"Querying LLM with {len(context_docs)} documents for {attempt_type}")
        response = llm.invoke(prompt)
        answer_text = response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

        if is_answer_failure(answer_text):
            logger.info(f"LLM indicated insufficient context for {attempt_type} attempt")
            return None

        logger.info(f"✅ Successfully generated answer using {attempt_type} approach")
        return {
            "answer": answer_text,
            "source_documents": context_docs,
            "search_method": attempt_type
        }
        
    except Exception as e:
        logger.error(f"Error calling LLM for {attempt_type}: {e}")
        return None


def search_tier(tier_name: str, index_path: str, query: str, threshold: float = SearchConfig.DEFAULT_THRESHOLD) -> Optional[Dict]:
    """Search a single tier with enhanced logging and error handling."""
    logger.info(f"🔍 Searching {tier_name}...")
    
    try:
        sources = search_vectorstore(index_path, query, threshold)
        if sources:
            result = ask_llm(query, sources, tier_name.lower().replace(" ", "_").replace("📄", "").replace("🌐", "").replace("🎬", "").strip())
            if result:
                logger.info(f"✅ Found answer in {tier_name}")
                result["tier"] = tier_name
                return result
            else:
                logger.info(f"❌ {tier_name} had {len(sources)} relevant docs but LLM couldn't generate answer")
        else:
            logger.info(f"❌ No relevant documents found in {tier_name}")
            
    except Exception as e:
        logger.error(f"Error searching {tier_name}: {e}")
        
    return None


def get_answer(query: str) -> Dict:
    """Enhanced tiered search with improved fallback logic and comprehensive error handling."""
    logger.info(f"🔍 Processing query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
    
    # Define search tiers with proper paths
    tiers = [
        ("📄 Local Documents", DOC_FAISS_PATH),
        ("🌐 Scraped Websites", SCRAPED_FAISS_PATH),
        ("🎬 YouTube Videos", YOUTUBE_FAISS_PATH)
    ]
    
    # Phase 1: Try each tier with standard threshold
    for tier_name, index_path in tiers:
        result = search_tier(tier_name, index_path, query, SearchConfig.DEFAULT_THRESHOLD)
        if result:
            return result
    
    # Phase 2: Relaxed search across all tiers
    logger.info("🔄 Phase 2: Retrying with relaxed similarity threshold...")
    all_docs = []
    
    for tier_name, index_path in tiers:
        try:
            docs = search_vectorstore(index_path, query, SearchConfig.RELAXED_THRESHOLD)
            if docs:
                logger.info(f"Found {len(docs)} additional docs in {tier_name} with relaxed threshold")
                # Add tier information to metadata
                for doc in docs:
                    doc.metadata["tier"] = tier_name
                all_docs.extend(docs)
        except Exception as e:
            logger.error(f"Error in relaxed search for {tier_name}: {e}")
    
    # Try combined context from all sources
    if all_docs:
        logger.info(f"🔄 Attempting answer with combined relaxed context ({len(all_docs)} total docs)")
        result = ask_llm(query, all_docs, "combined_relaxed")
        if result:
            result["tier"] = "Combined Sources (Relaxed)"
            return result
    
    # Phase 3: Emergency threshold search
    logger.info("🆘 Phase 3: Emergency threshold search...")
    emergency_docs = []
    
    for tier_name, index_path in tiers:
        try:
            docs = search_vectorstore(index_path, query, SearchConfig.EMERGENCY_THRESHOLD)
            if docs:
                logger.info(f"Found {len(docs)} docs in {tier_name} with emergency threshold")
                for doc in docs:
                    doc.metadata["tier"] = tier_name
                emergency_docs.extend(docs)
        except Exception as e:
            logger.error(f"Error in emergency search for {tier_name}: {e}")
    
    if emergency_docs:
        logger.info(f"🆘 Attempting answer with emergency threshold ({len(emergency_docs)} total docs)")
        result = ask_llm(query, emergency_docs, "emergency_combined")
        if result:
            result["tier"] = "Emergency Search (Very Relaxed)"
            return result
    
    # Phase 4: Web search fallback with enhanced error handling
    logger.info("🌐 Phase 4: Falling back to Internet search...")
    try:
        web_results = search_tavily(query)
        
        if not web_results:
            logger.warning("Web search returned no results")
            return {
                "answer": "I couldn't find relevant information in my MeitY knowledge base or through web search. Please try rephrasing your question with more specific terms related to Ministry of Electronics and IT, digital initiatives, or technology policies.",
                "source_documents": [],
                "tier": "No Results",
                "search_method": "failed"
            }
        
        # Handle different possible return formats from Tavily
        web_docs = []
        if isinstance(web_results, list):
            for i, res in enumerate(web_results):
                if isinstance(res, dict):
                    content = res.get('content', res.get('snippet', ''))
                    url = res.get('url', f'Web Result {i+1}')
                    title = res.get('title', 'Web Search Result')
                    
                    if content:  # Only add if there's actual content
                        doc = Document(
                            page_content=content,
                            metadata={
                                'source': url,
                                'title': title,
                                'type': 'web_search',
                                'tier': 'Web Search'
                            }
                        )
                        web_docs.append(doc)
                else:
                    # Handle string results or other formats
                    doc = Document(
                        page_content=str(res),
                        metadata={
                            'source': f'Web Result {i+1}',
                            'title': 'Web Search Result',
                            'type': 'web_search',
                            'tier': 'Web Search'
                        }
                    )
                    web_docs.append(doc)
        
        if web_docs:
            logger.info(f"Found {len(web_docs)} web results, attempting to synthesize answer")
            result = ask_llm(query, web_docs, "web_fallback")
            
            if result:
                result["tier"] = "Web Search"
                return result
            else:
                # LLM couldn't synthesize, but we have sources
                return {
                    "answer": "I found some information online but couldn't synthesize a clear answer from the MeitY context. Please review the sources provided below for more details, or try rephrasing your question.",
                    "source_documents": web_docs,
                    "tier": "Web Search (Raw Results)",
                    "search_method": "web_raw"
                }
        else:
            logger.warning("No valid content found in web search results")
            return {
                "answer": "Web search completed but didn't return usable content. Please try rephrasing your question or adding more specific terms related to MeitY or Indian technology policies.",
                "source_documents": [],
                "tier": "Web Search Failed",
                "search_method": "web_empty"
            }
        
    except Exception as e:
        logger.error(f"Web search failed with error: {e}")
        return {
            "answer": f"An error occurred during web search: {str(e)}. This might be due to network issues or API limitations. Please try again later, or contact support if the problem persists.",
            "source_documents": [],
            "tier": "Web Search Error",
            "search_method": "web_error"
        }


def health_check() -> Dict[str, any]:
    """Enhanced health check with detailed status information."""
    status = {
        "embeddings_loaded": False,
        "doc_index_available": False,
        "scraped_index_available": False,
        "youtube_index_available": False,
        "llm_accessible": False,
        "tavily_configured": False,
        "details": {}
    }
    
    # Check embeddings
    try:
        test_embedding = embeddings.embed_query("test query")
        status["embeddings_loaded"] = len(test_embedding) > 0
        status["details"]["embedding_dimension"] = len(test_embedding)
    except Exception as e:
        status["details"]["embedding_error"] = str(e)
    
    # Check indexes with document counts
    for index_name, path_var, status_key in [
        ("Documents", DOC_FAISS_PATH, "doc_index_available"),
        ("Scraped", SCRAPED_FAISS_PATH, "scraped_index_available"),
        ("YouTube", YOUTUBE_FAISS_PATH, "youtube_index_available")
    ]:
        faiss_file = os.path.join(path_var, "index.faiss")
        if os.path.exists(faiss_file):
            status[status_key] = True
            try:
                # Try to load and get document count
                vectordb = FAISS.load_local(path_var, embeddings, allow_dangerous_deserialization=True)
                status["details"][f"{index_name.lower()}_count"] = vectordb.index.ntotal
            except Exception as e:
                status["details"][f"{index_name.lower()}_error"] = str(e)
        else:
            status["details"][f"{index_name.lower()}_path"] = f"Missing: {faiss_file}"
    
    # Check LLM
    try:
        llm = ChatTogether(model="mistralai/Mistral-7B-Instruct-v0.2", temperature=0.1)
        response = llm.invoke("Say 'OK' if you can process this.")
        status["llm_accessible"] = "ok" in response.content.lower()
        status["details"]["llm_response"] = response.content[:100]
    except Exception as e:
        status["details"]["llm_error"] = str(e)
    
    # Check Tavily API
    tavily_key = os.environ.get("TAVILY_API_KEY")
    status["tavily_configured"] = bool(tavily_key)
    if not tavily_key:
        status["details"]["tavily_error"] = "TAVILY_API_KEY environment variable not set"
        
    return status


# Export the main function for external use
__all__ = ['get_answer', 'health_check']