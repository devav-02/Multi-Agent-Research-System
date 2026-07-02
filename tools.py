from langchain.tools import tool 
import requests
from firecrawl import FirecrawlApp
from tavily import TavilyClient
import os 
from dotenv import load_dotenv
from rich import print
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query : str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    results = tavily.search(query=query,max_results=5)

    out = []

    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )
    
    return "\n----\n".join(out)


firecrawl = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_API_KEY")
)

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        result = firecrawl.scrape_url(url=url, formats=["markdown"])
        content = result.markdown or ""
        return content.strip()[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"