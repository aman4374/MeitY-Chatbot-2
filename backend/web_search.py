import os
import logging
from typing import List, Dict, Optional
from langchain_community.tools.tavily_search import TavilySearchResults

# Set up logging
logger = logging.getLogger(__name__)

def search_tavily(query: str, max_results: int = 5) -> List[Dict]:
    """
    Performs a web search using the Tavily API with enhanced error handling
    and better result formatting.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        List of dictionaries containing search results with keys:
        - content: Main text content
        - url: Source URL  
        - title: Page title
        - score: Relevance score (if available)
    """
    
    # Check API key
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.error("Tavily API key is not set in environment variables")
        return []
    
    try:
        logger.info(f"Performing Tavily search for: '{query}' (max_results: {max_results})")
        
        # Initialize Tavily search tool
        tool = TavilySearchResults(
            max_results=max_results,
            search_depth="advanced",  # Use advanced search for better results
            include_answer=True,      # Include AI-generated answer
            include_raw_content=False # Don't include raw HTML
        )
        
        # Perform search
        raw_results = tool.invoke(query)
        
        if not raw_results:
            logger.warning("Tavily search returned no results")
            return []
        
        # Process and standardize results
        processed_results = []
        
        # Handle different possible result formats
        if isinstance(raw_results, list):
            for i, result in enumerate(raw_results):
                if isinstance(result, dict):
                    processed_result = process_tavily_result(result, i)
                    if processed_result:
                        processed_results.append(processed_result)
                else:
                    # Handle non-dict results
                    logger.warning(f"Unexpected result format at index {i}: {type(result)}")
                    processed_results.append({
                        "content": str(result),
                        "url": f"Search Result {i + 1}",
                        "title": f"Web Search Result {i + 1}",
                        "score": None
                    })
        
        elif isinstance(raw_results, dict):
            # Single result returned as dict
            processed_result = process_tavily_result(raw_results, 0)
            if processed_result:
                processed_results.append(processed_result)
        
        else:
            # Unexpected format
            logger.warning(f"Unexpected Tavily result format: {type(raw_results)}")
            processed_results.append({
                "content": str(raw_results),
                "url": "Web Search Result",
                "title": "Search Result",
                "score": None
            })
        
        # Filter out empty or very short content
        filtered_results = []
        for result in processed_results:
            content = result.get("content", "").strip()
            if content and len(content) > 50:  # Minimum content length
                filtered_results.append(result)
            else:
                logger.debug(f"Filtered out result with insufficient content: {result.get('title', 'Unknown')}")
        
        logger.info(f"Tavily search completed: {len(filtered_results)} usable results from {len(processed_results)} total")
        
        return filtered_results
        
    except Exception as e:
        logger.error(f"Error during Tavily search: {str(e)}")
        
        # Try to provide more specific error information
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg:
            logger.error("Authentication error - check TAVILY_API_KEY")
        elif "rate limit" in error_msg or "quota" in error_msg:
            logger.error("Rate limit exceeded - try again later")
        elif "network" in error_msg or "connection" in error_msg:
            logger.error("Network connectivity issue")
        else:
            logger.error(f"Unknown error during Tavily search: {e}")
        
        return []


def process_tavily_result(result: Dict, index: int) -> Optional[Dict]:
    """
    Process a single Tavily search result and standardize the format.
    
    Args:
        result: Raw result dictionary from Tavily
        index: Result index for fallback naming
    
    Returns:
        Standardized result dictionary or None if invalid
    """
    
    try:
        # Extract content with fallbacks
        content = None
        
        # Try different possible content keys
        for content_key in ['content', 'snippet', 'body', 'text', 'description']:
            if content_key in result and result[content_key]:
                content = str(result[content_key]).strip()
                break
        
        if not content:
            logger.debug(f"No content found in result {index}")
            return None
        
        # Extract URL
        url = result.get('url', result.get('link', f'Search Result {index + 1}'))
        
        # Extract title with fallbacks
        title = result.get('title', result.get('name', ''))
        if not title:
            # Generate title from URL or content
            if isinstance(url, str) and url.startswith('http'):
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    title = f"Result from {domain}"
                except:
                    title = f"Web Search Result {index + 1}"
            else:
                title = f"Search Result {index + 1}"
        
        # Extract relevance score if available
        score = result.get('score', result.get('relevance', None))
        if score is not None:
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = None
        
        # Clean up content
        content = clean_content(content)
        
        processed_result = {
            "content": content,
            "url": str(url),
            "title": str(title).strip(),
            "score": score
        }
        
        # Add any additional metadata
        if 'published_date' in result:
            processed_result['published_date'] = result['published_date']
        
        if 'source' in result and result['source'] != url:
            processed_result['source_name'] = str(result['source'])
        
        return processed_result
        
    except Exception as e:
        logger.error(f"Error processing Tavily result {index}: {e}")
        return None


def clean_content(content: str) -> str:
    """
    Clean and normalize content text.
    
    Args:
        content: Raw content string
    
    Returns:
        Cleaned content string
    """
    
    if not content:
        return ""
    
    # Remove extra whitespace
    content = " ".join(content.split())
    
    # Remove common web artifacts
    artifacts_to_remove = [
        "Click here to read more",
        "Read more...",
        "Continue reading",
        "Advertisement",
        "Subscribe to newsletter",
        "Cookie policy",
        "Privacy policy"
    ]
    
    for artifact in artifacts_to_remove:
        content = content.replace(artifact, "")
    
    # Limit content length to avoid overwhelming the LLM
    max_length = 1500  # Reasonable limit for each search result
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    return content.strip()


def test_tavily_connection() -> Dict[str, any]:
    """
    Test Tavily API connection and return status information.
    
    Returns:
        Dictionary with connection status and details
    """
    
    status = {
        "api_key_configured": False,
        "connection_successful": False,
        "test_query_results": 0,
        "error_message": None
    }
    
    # Check API key
    api_key = os.environ.get("TAVILY_API_KEY")
    status["api_key_configured"] = bool(api_key)
    
    if not api_key:
        status["error_message"] = "TAVILY_API_KEY environment variable not set"
        return status
    
    # Test with a simple query
    try:
        results = search_tavily("test query", max_results=1)
        status["connection_successful"] = True
        status["test_query_results"] = len(results)
        
        if not results:
            status["error_message"] = "API connected but no results returned for test query"
        else:
            logger.info("Tavily connection test successful")
            
    except Exception as e:
        status["error_message"] = str(e)
        logger.error(f"Tavily connection test failed: {e}")
    
    return status


# Additional utility function for debugging
def search_tavily_debug(query: str, max_results: int = 3) -> Dict:
    """
    Debug version of search_tavily that returns additional diagnostic information.
    
    Returns:
        Dictionary with:
        - results: List of search results
        - debug_info: Additional diagnostic information
    """
    
    debug_info = {
        "query": query,
        "max_results": max_results,
        "api_key_configured": bool(os.environ.get("TAVILY_API_KEY")),
        "raw_results_type": None,
        "processing_errors": [],
        "filtered_count": 0
    }
    
    try:
        results = search_tavily(query, max_results)
        debug_info["filtered_count"] = len(results)
        
        return {
            "results": results,
            "debug_info": debug_info
        }
        
    except Exception as e:
        debug_info["processing_errors"].append(str(e))
        return {
            "results": [],
            "debug_info": debug_info
        }


# Export main functions
__all__ = ['search_tavily', 'test_tavily_connection', 'search_tavily_debug']