# import os
# from langchain_community.tools.tavily_search import TavilySearchResults

# def search_tavily(query: str) -> str:
#     """
#     Performs a web search using the Tavily API and returns a formatted string of results.
#     """
#     api_key = os.environ.get("TAVILY_API_KEY")
#     if not api_key:
#         return "Tavily API key is not set in environment variables. Cannot perform web search."

#     # Initialize the tool to get a maximum of 3 results
#     tool = TavilySearchResults(max_results=3)
    
#     # Get the search results
#     results = tool.invoke(query)
    
#     # Format the results into a readable string
#     if not results:
#         return "No relevant results found from the web search."

#     formatted_results = []
#     for i, res in enumerate(results):
#         formatted_results.append(f"Result {i+1}:\nContent: {res['content']}\nSource: {res['url']}")
    
#     return "\n\n".join(formatted_results)

import os
from langchain_community.tools.tavily_search import TavilySearchResults

def search_tavily(query: str) -> list[dict]:
    """
    Performs a web search using the Tavily API and returns the raw results.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("Tavily API key is not set.")
        return []

    tool = TavilySearchResults(max_results=3)
    results = tool.invoke(query)
    return results