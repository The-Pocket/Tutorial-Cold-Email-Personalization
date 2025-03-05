"""
Web Search Utility for Cold Outreach Opener Generator
"""
import os
import requests
import json

def search_web(query, num_results=10):
    """
    Executes a Google Custom Search and returns results.
    :param api_key: Your Google API key
    :param cse_id: Your custom search engine ID
    :param query: The search query string
    :param num_results: Number of search results to return (1-10)
    :return: A list of results (each result is a dict with relevant fields)
    """
    # Replace these with your actual API key and Search Engine ID.
    API_KEY = "google-api-key"
    SEARCH_ENGINE_ID = "google-search-engine-id"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': num_results
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        # Results are typically in data['items'] if the request is successful
        return data.get('items', [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

if __name__ == "__main__":
    results = search_web("Elon Musk")
    
    for idx, item in enumerate(results, start=1):
        title = item.get("title")
        snippet = item.get("snippet")
        link = item.get("link")
        print(f"{idx}. {title}\n{snippet}\nLink: {link}\n")
