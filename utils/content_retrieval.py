"""
HTML Content Retrieval Utility for Cold Outreach Opener Generator
"""
import requests
from bs4 import BeautifulSoup

def get_html_content(url, timeout=10):
    """
    Retrieves HTML content from a URL.
    
    Args:
        url (str): URL to retrieve content from
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        
    Returns:
        dict: Dictionary containing HTML content and extracted text
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Extract text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text (remove excessive newlines)
        lines = (line.strip() for line in text.splitlines())
        text = ' '.join(line for line in lines if line)
        
        return {
            "html": html_content,
            "text": text,
            "title": soup.title.string if soup.title else ""
        }
    except Exception as e:
        print(f"Error retrieving content from {url}: {e}")
        return {
            "html": "",
            "text": f"Error retrieving content: {str(e)}",
            "title": ""
        }

if __name__ == "__main__":
    # Test the function
    test_url = "https://github.com/The-Pocket/PocketFlow"
    content = get_html_content(test_url)
    print(f"Title: {content['title']}")
    print(f"Text length: {len(content['text'])}")
    print("First 200 characters of text:")
    print(content['text'][:200] + "...") 