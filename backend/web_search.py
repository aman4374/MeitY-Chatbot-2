import os
import requests

def search_tavily(query: str) -> str:
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "⚠️ Tavily API key is missing in .env file."

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 3
    }
    try:
        response = requests.post(url, json=payload)
        result = response.json()

        answer = result.get("answer", "❌ No internet answer found.")

        sources = result.get("results", [])
        if sources:
            links = "\n".join([f"- [{s['title']}]({s['url']})" for s in sources])
            return f"{answer}\n\n🔗 Sources:\n{links}"
        else:
            return answer

    except Exception as e:
        return f"⚠️ Tavily API failed: {e}"