import asyncio
from duckduckgo_search import DDGS
from typing import List, Dict

async def search_web_for_paper(title: str, authors: List[str] = None) -> List[Dict]:
    """
    Searches the web for discussions, reception, and impact of a paper.
    """
    if not title:
        return []
        
    author_str = ""
    if authors and len(authors) > 0:
        if isinstance(authors[0], dict) and "name" in authors[0]:
            author_str = authors[0]["name"]
        elif isinstance(authors[0], str):
            author_str = authors[0]

    query = f'"{title}"'
    if author_str:
        query += f' "{author_str}"'
    
    # Add keywords to find discussions/impact
    query += ' (github OR reddit OR blog OR review OR impact OR breakthrough)'

    print(f"Executing web search with query: {query}")
    
    def sync_search():
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
                return results
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return []

    # Run the synchronous search in a thread pool
    results = await asyncio.to_thread(sync_search)
    return results
