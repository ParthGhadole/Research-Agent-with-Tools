from serpapi import Client
import os
from dotenv import load_dotenv
load_dotenv(".env")
import httpx
import json 
def filter_search_results(results_list):
    filtered_output = []
    
    for item in results_list:
        pub_info = item.get("publication_info", {})
        inline_links = item.get("inline_links", {})
        
        filtered_item = {
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
            "authors": [a.get("name") for a in pub_info.get("authors", [])],
            "year": pub_info.get("summary", "").split(" - ")[1] if " - " in pub_info.get("summary", "") else None,
            "source": pub_info.get("summary", "").split(" - ")[-1] if " - " in pub_info.get("summary", "") else None,
            "citations": inline_links.get("cited_by", {}).get("total", 0)
        }
        filtered_output.append(filtered_item)
        
    return filtered_output


def web_search_tool_sync(query: str) -> list:
    """
    Returns global search urls.
    Args:
        query (str): The search term.
    Returns:
        list: A list of urls from global search.
    """    
    params = {
        "engine": "google_scholar",
        "q": query,
        "hl": "en",
        "as_ylo": "2019"
    }
    search_client = Client(api_key=os.getenv("SERP_API_KEY"))
    results = search_client.search(params)
    return filter_search_results(results["google_scholar"])


from langchain_core.tools import tool
@tool
async def web_search_tool(query: str) -> list:
    """
    Returns global search urls.
    Args:
        query (str): The search term.
    Returns:
        list: A list of urls from global search.
    """

    if query == "machine learning" or "machine learning" in query.lower():
        with open("data/cleaned_data.json", "r") as f:
            cleaned_data = json.load(f)
        return cleaned_data
    
    params = {
        "engine": "google_scholar",
        "q": query,
        "hl": "en",
        "as_ylo": "2019",
        "api_key": os.getenv("SERP_API_KEY")
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get("https://serpapi.com/search", params=params)
        results = response.json()
        
    return filter_search_results(results["google_scholar"])