from duckduckgo_search import DDGS

def get_stock_news(ticker, limit=5):
    """
    Fetches the latest news for a given stock ticker using DuckDuckGo.
    """
    try:
        # Query specifically for stock news
        query = f"{ticker} stock news latest financial"
        
        results = []
        # Use the context manager for DDGS
        with DDGS() as ddgs:
            # Fetch news results
            news_gen = ddgs.news(keywords=query, max_results=limit)
            
            for r in news_gen:
                results.append({
                    'title': r.get('title', 'No title'),
                    'source': r.get('source', 'Unknown Source'),
                    'date': r.get('date', ''),
                    'url': r.get('url', '#'),
                    'body': r.get('body', '')
                })
                
        return results
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

def format_news_for_llm(news_items):
    """
    Formats the news list into a string for the LLM prompt.
    """
    if not news_items:
        return "No recent news found."
        
    formatted = "\nRecent News & Headlines:\n"
    for i, item in enumerate(news_items, 1):
        formatted += f"{i}. {item['title']} (Source: {item['source']})\n"
        # Add a brief snippet if available, truncated to avoid token limits
        if item['body']:
            snippet = item['body'][:150] + "..." if len(item['body']) > 150 else item['body']
            formatted += f"   Summary: {snippet}\n"
            
    return formatted

