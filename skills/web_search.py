#!/usr/bin/env python3
"""
网页搜索 (Web Search). Real-time web search using DuckDuckGo HTML endpoint.
Parameters:
  --query: The search query.
"""
import urllib.request
import urllib.parse
import sys
import json
import argparse
import re

def search_duckduckgo(query: str) -> dict:
    if not query:
        return {"error": "Query is required"}
        
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {
            "status": "degraded",
            "message": "Python module 'beautifulsoup4' not found. Please run 'pip install beautifulsoup4'.",
            "results": []
        }

    try:
        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({'q': query}).encode('ascii')
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10.0) as response:
            html = response.read().decode('utf-8')
            
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        for result in soup.select(".result"):
            title_tag = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            
            if title_tag and snippet_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href")
                snippet = snippet_tag.get_text(strip=True)
                
                if link and not link.startswith("//"):
                    if 'uddg=' in link:
                        try:
                            link = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])
                        except Exception:
                            pass
                    results.append({"title": title, "snippet": snippet, "link": link})
                    
            if len(results) >= 10:
                break
                
        return {"status": "success", "results": results}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Search Skill via DuckDuckGo")
    parser.add_argument("--query", type=str, required=True, help="The search query.")
    args = parser.parse_args()
    
    result = search_duckduckgo(args.query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
