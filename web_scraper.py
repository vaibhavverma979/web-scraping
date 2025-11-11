"""
Interactive Web Scraping Script using requests and BeautifulSoup
This script allows you to extract specific text, images, or links from any webpage.
You can search for text by keywords (e.g., "about us", "notice", "alert") 
and select specific images from the website.
Now includes AI-powered topic extraction using OpenAI's function calling.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, Union, List, Dict
import re
import os
import json

# Try to import openai, if not available, the AI feature will be disabled
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai library not installed. AI features will be disabled.")
    print("Install it with: pip install openai")


def get_page_content(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch and parse webpage content.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        Optional[BeautifulSoup]: Parsed HTML content or None if error
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching data from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def search_text_by_keyword(url: str, keyword: str, case_sensitive: bool = False) -> Union[str, List[str], None]:
    """
    Search for text containing a specific keyword (e.g., "about us", "notice", "alert").
    
    Args:
        url (str): The URL to scrape
        keyword (str): The keyword to search for
        case_sensitive (bool): Whether the search should be case-sensitive
        
    Returns:
        Union[str, List[str], None]: Found text(s) or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Find all text elements containing the keyword
    found_texts = []
    keyword_lower = keyword.lower() if not case_sensitive else keyword
    
    # Search in all text elements
    all_text_elements = soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'article', 'section'])
    
    for element in all_text_elements:
        text = element.get_text(strip=True)
        if text:
            text_to_search = text.lower() if not case_sensitive else text
            if keyword_lower in text_to_search:
                # Get the full text of the element and its parent context
                full_text = element.get_text(separator=' ', strip=True)
                if full_text and full_text not in found_texts:
                    found_texts.append(full_text)
    
    # Also search in alt text and titles
    for img in soup.find_all('img', alt=True):
        alt_text = img.get('alt', '')
        if alt_text:
            alt_to_search = alt_text.lower() if not case_sensitive else alt_text
            if keyword_lower in alt_to_search:
                context = f"[Image Alt Text] {alt_text}"
                if context not in found_texts:
                    found_texts.append(context)
    
    if found_texts:
        return found_texts[0] if len(found_texts) == 1 else found_texts
    else:
        return f"Not found - No text containing '{keyword}' was found"


def list_all_images(url: str) -> List[str]:
    """
    List all image URLs on the page.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        List[str]: List of image URLs
    """
    soup = get_page_content(url)
    if not soup:
        return []
    
    def normalize_image_url(img_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not img_url:
            return ""
        if img_url.startswith('//'):
            return 'https:' + img_url
        elif img_url.startswith('http://') or img_url.startswith('https://'):
            return img_url
        elif img_url.startswith('/'):
            return urljoin(url, img_url)
        else:
            return urljoin(url, img_url)
    
    images = []
    img_tags = soup.find_all('img')
    
    for idx, img in enumerate(img_tags, 1):
        img_url = (img.get('src') or 
                  img.get('data-src') or 
                  img.get('data-lazy-src') or
                  img.get('data-original') or
                  img.get('data-url'))
        
        if img_url:
            img_url = normalize_image_url(img_url)
            if img_url and img_url not in images:
                images.append(img_url)
    
    return images


def search_image_by_keyword(url: str, keyword: str) -> List[str]:
    """
    Search for images containing a specific keyword in alt text, title, or nearby text.
    
    Args:
        url (str): The URL to scrape
        keyword (str): The keyword to search for
        
    Returns:
        List[str]: List of image URLs (empty list if none found)
    """
    soup = get_page_content(url)
    if not soup:
        return []
    
    def normalize_image_url(img_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not img_url:
            return ""
        if img_url.startswith('//'):
            return 'https:' + img_url
        elif img_url.startswith('http://') or img_url.startswith('https://'):
            return img_url
        elif img_url.startswith('/'):
            return urljoin(url, img_url)
        else:
            return urljoin(url, img_url)
    
    keyword_lower = keyword.lower()
    found_images = []
    
    # Search in img tags
    for img in soup.find_all('img'):
        alt_text = img.get('alt', '').lower()
        title_text = img.get('title', '').lower()
        class_text = ' '.join(img.get('class', [])).lower()
        
        # Check if keyword is in alt, title, or class
        if (keyword_lower in alt_text or 
            keyword_lower in title_text or 
            keyword_lower in class_text):
            
            img_url = (img.get('src') or 
                      img.get('data-src') or 
                      img.get('data-lazy-src') or
                      img.get('data-original') or
                      img.get('data-url'))
            
            if img_url:
                normalized_url = normalize_image_url(img_url)
                if normalized_url and normalized_url not in found_images:
                    found_images.append(normalized_url)
        
        # Also check nearby text (parent elements)
        parent = img.find_parent(['div', 'section', 'article', 'figure'])
        if parent:
            parent_text = parent.get_text(strip=True).lower()
            if keyword_lower in parent_text:
                img_url = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          img.get('data-url'))
                
                if img_url:
                    normalized_url = normalize_image_url(img_url)
                    if normalized_url and normalized_url not in found_images:
                        found_images.append(normalized_url)
    
    return found_images


def scrape_text_with_selector(url: str, selector: Optional[str] = None) -> Union[str, List[str], None]:
    """
    Extract text using CSS selector.
    
    Args:
        url (str): The URL to scrape
        selector (Optional[str]): CSS selector for the text element
        
    Returns:
        Union[str, List[str], None]: Extracted text or list of texts, or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    if selector:
        elements = soup.select(selector)
        if elements:
            texts = [elem.get_text(strip=True) for elem in elements]
            return texts[0] if len(texts) == 1 else texts
        else:
            return "Not found - No elements matched the selector"
    else:
        # Try common text selectors
        selectors = ['h1', 'h1.title', '.product-title', '.title', '[class*="title"]', 'h2']
        for sel in selectors:
            elements = soup.select(sel)
            if elements:
                texts = [elem.get_text(strip=True) for elem in elements]
                return texts[0] if len(texts) == 1 else texts
        return "Not found - Could not find any text elements"


def scrape_image_with_selector(url: str, selector: Optional[str] = None) -> Union[str, List[str], None]:
    """
    Extract image URL(s) using CSS selector.
    
    Args:
        url (str): The URL to scrape
        selector (Optional[str]): CSS selector for the image element
        
    Returns:
        Union[str, List[str], None]: Extracted image URL(s), or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    def normalize_image_url(img_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not img_url:
            return ""
        if img_url.startswith('//'):
            return 'https:' + img_url
        elif img_url.startswith('http://') or img_url.startswith('https://'):
            return img_url
        elif img_url.startswith('/'):
            return urljoin(url, img_url)
        else:
            return urljoin(url, img_url)
    
    if selector:
        elements = soup.select(selector)
        if elements:
            images = []
            for img in elements:
                img_url = (img.get('src') or 
                          img.get('data-src') or 
                          img.get('data-lazy-src') or
                          img.get('data-original') or
                          img.get('data-url'))
                if img_url:
                    images.append(normalize_image_url(img_url))
            
            if images:
                return images[0] if len(images) == 1 else images
            else:
                return "Not found - No image URLs found in selected elements"
        else:
            return "Not found - No elements matched the selector"
    else:
        # Try common image selectors
        selectors = [
            'img[class*="main"]',
            'img[class*="product"]',
            'img[class*="primary"]',
            'img[class*="featured"]',
            '.product-image img',
            '.main-image img',
            'img'
        ]
        
        for sel in selectors:
            elements = soup.select(sel)
            if elements:
                images = []
                for img in elements:
                    img_url = (img.get('src') or 
                              img.get('data-src') or 
                              img.get('data-lazy-src') or
                              img.get('data-original') or
                              img.get('data-url'))
                    if img_url and not img_url.endswith('.svg'):
                        images.append(normalize_image_url(img_url))
                
                if images:
                    return images[0] if len(images) == 1 else images
        
        return "Not found - Could not find any image elements"


def search_link_by_keyword(url: str, keyword: str) -> Union[str, List[str], None]:
    """
    Search for links containing a specific keyword in text or URL.
    
    Args:
        url (str): The URL to scrape
        keyword (str): The keyword to search for
        
    Returns:
        Union[str, List[str], None]: Link URL(s) or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    def normalize_link_url(link_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not link_url:
            return ""
        if link_url.startswith('//'):
            return 'https:' + link_url
        elif link_url.startswith('http://') or link_url.startswith('https://'):
            return link_url
        elif link_url.startswith('/'):
            return urljoin(url, link_url)
        elif link_url.startswith('#'):
            return url + link_url
        else:
            return urljoin(url, link_url)
    
    keyword_lower = keyword.lower()
    found_links = []
    
    # Search in all anchor tags
    for link in soup.find_all('a', href=True):
        link_text = link.get_text(strip=True).lower()
        href = link.get('href', '')
        href_lower = href.lower()
        title = link.get('title', '').lower()
        class_text = ' '.join(link.get('class', [])).lower()
        
        # Check if keyword is in link text, href, title, or class
        if (keyword_lower in link_text or 
            keyword_lower in href_lower or 
            keyword_lower in title or 
            keyword_lower in class_text):
            
            if href and not href.startswith('javascript:'):
                normalized_url = normalize_link_url(href)
                if normalized_url and normalized_url not in found_links:
                    found_links.append(normalized_url)
    
    if found_links:
        return found_links[0] if len(found_links) == 1 else found_links
    else:
        return f"Not found - No links containing '{keyword}' were found"


def scrape_section_by_heading(url: str, heading_keyword: str) -> Union[str, None]:
    """
    Extract a section of content by finding a heading containing the keyword
    and returning all subsequent content until the next heading.
    
    Args:
        url (str): The URL to scrape
        heading_keyword (str): The keyword to search for in h2/h3 headings (case-insensitive)
        
    Returns:
        Union[str, None]: The extracted section text or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    heading_keyword_lower = heading_keyword.lower()
    
    # Find all h2 and h3 headings
    headings = soup.find_all(['h2', 'h3'])
    
    # Search for a heading containing the keyword
    target_heading = None
    target_index = -1
    for idx, heading in enumerate(headings):
        heading_text = heading.get_text(strip=True).lower()
        if heading_keyword_lower in heading_text:
            target_heading = heading
            target_index = idx
            break
    
    if not target_heading:
        return f"Not found - No heading containing '{heading_keyword}' was found"
    
    # Collect all content after the target heading until the next h2/h3
    content_parts = []
    
    # Method 1: Get all elements in the document and find content between headings
    all_elements = soup.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'div', 'article', 'section'])
    
    # Find the position of target heading and next heading
    start_collecting = False
    for elem in all_elements:
        # Start collecting when we find the target heading
        if elem == target_heading:
            start_collecting = True
            continue
        
        # Stop if we hit another heading
        if start_collecting and elem.name in ['h2', 'h3']:
            break
        
        # Collect content
        if start_collecting:
            if elem.name in ['p', 'ul', 'ol', 'div', 'article', 'section']:
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text.strip()) > 0:
                    content_parts.append(text)
    
    # Method 2: If Method 1 didn't work, try traversing siblings
    if not content_parts:
        # Try to get next siblings of the heading's parent
        parent = target_heading.parent
        if parent:
            # Get all next siblings of the parent until we hit a heading
            for sibling in parent.next_siblings:
                if hasattr(sibling, 'name'):
                    if sibling.name in ['h2', 'h3']:
                        break
                    elif sibling.name in ['p', 'ul', 'ol', 'div', 'article', 'section']:
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            content_parts.append(text)
                elif hasattr(sibling, 'find_all'):
                    # It's a Tag, find content elements
                    for elem in sibling.find_all(['p', 'ul', 'ol', 'div']):
                        if elem.find_parent(['h2', 'h3']) is None:  # Not nested in another heading
                            text = elem.get_text(separator=' ', strip=True)
                            if text:
                                content_parts.append(text)
                    # Check if this sibling contains a heading (stop condition)
                    if sibling.find(['h2', 'h3']):
                        break
    
    # Method 3: Get all text from the heading's next siblings directly
    if not content_parts:
        current = target_heading
        # Try to find the container (article, main, or body)
        container = current.find_parent(['article', 'main', 'section', 'body'])
        if not container:
            container = soup.body if soup.body else soup
        
        # Get all elements after the heading
        found_heading = False
        for elem in container.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'div', 'article', 'section']):
            if elem == target_heading:
                found_heading = True
                continue
            
            if found_heading:
                if elem.name in ['h2', 'h3']:
                    break
                elif elem.name in ['p', 'ul', 'ol', 'div', 'article', 'section']:
                    text = elem.get_text(separator=' ', strip=True)
                    if text:
                        content_parts.append(text)
    
    if content_parts:
        # Join and clean up the text, removing duplicates
        seen_texts = set()
        unique_parts = []
        for part in content_parts:
            # Normalize the text
            normalized = ' '.join(part.split())
            if normalized and normalized not in seen_texts and len(normalized) > 10:
                seen_texts.add(normalized)
                unique_parts.append(normalized)
        
        if unique_parts:
            result_text = ' '.join(unique_parts)
            return result_text
    
    return f"Found heading '{target_heading.get_text(strip=True)}' but no content found below it"


def scrape_link_with_selector(url: str, selector: Optional[str] = None) -> Union[str, List[str], None]:
    """
    Extract link URL(s) using CSS selector.
    
    Args:
        url (str): The URL to scrape
        selector (Optional[str]): CSS selector for the link element
        
    Returns:
        Union[str, List[str], None]: Extracted link URL(s), or None if error
    """
    soup = get_page_content(url)
    if not soup:
        return None
    
    def normalize_link_url(link_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not link_url:
            return ""
        if link_url.startswith('//'):
            return 'https:' + link_url
        elif link_url.startswith('http://') or link_url.startswith('https://'):
            return link_url
        elif link_url.startswith('/'):
            return urljoin(url, link_url)
        elif link_url.startswith('#'):
            return url + link_url
        else:
            return urljoin(url, link_url)
    
    if selector:
        elements = soup.select(selector)
        if elements:
            links = []
            for link in elements:
                href = link.get('href')
                if href and not href.startswith('javascript:'):
                    links.append(normalize_link_url(href))
            
            if links:
                return links[0] if len(links) == 1 else links
            else:
                return "Not found - No links found in selected elements"
        else:
            return "Not found - No elements matched the selector"
    else:
        # Try common link selectors
        selectors = [
            'a[href*="cart"]',
            'a[href*="buy"]',
            'a[href*="add"]',
            'a[class*="button"]',
            'a[class*="btn"]',
            '.button a',
            '.btn a',
            'a[href]'
        ]
        
        for sel in selectors:
            elements = soup.select(sel)
            if elements:
                links = []
                for link in elements:
                    href = link.get('href')
                    if href and not href.startswith('javascript:'):
                        links.append(normalize_link_url(href))
                
                if links:
                    return links[0] if len(links) == 1 else links
        
        return "Not found - Could not find any link elements"


def ai_scrape_topic(url: str, topic_query: str, api_key: Optional[str] = None) -> str:
    """
    Use AI (OpenAI) to intelligently determine the best heading keyword from a natural language query
    and extract the corresponding section.
    
    Args:
        url (str): The URL to scrape
        topic_query (str): Natural language query (e.g., "Summarize the latest developments on Tesla's Gigafactories")
        api_key (Optional[str]): OpenAI API key. If None, will try to get from environment variable OPENAI_API_KEY
        
    Returns:
        str: The extracted section text or error message
    """
    if not OPENAI_AVAILABLE:
        return "Error: OpenAI library is not installed. Please install it with: pip install openai"
    
    # Get API key from parameter, config file, or environment variable
    if api_key is None:
        # First, try to get from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            api_key = api_key.strip()  # Remove whitespace
        
        # If not in environment, try to load from config.py file
        if not api_key:
            try:
                # Try to import config.py if it exists
                import sys
                import importlib.util
                config_path = os.path.join(os.path.dirname(__file__), 'config.py')
                if os.path.exists(config_path):
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config)
                    if hasattr(config, 'OPENAI_API_KEY'):
                        loaded_key = config.OPENAI_API_KEY
                        # Check if it's a valid key (not placeholder)
                        if loaded_key and loaded_key != "YOUR_OPENAI_API_KEY_HERE" and loaded_key.strip():
                            api_key = loaded_key.strip()  # Remove any whitespace
                            print(f"✓ API key loaded from config.py (length: {len(api_key)})")
                else:
                    print(f"⚠ config.py not found at: {config_path}")
            except Exception as e:
                print(f"⚠ Error loading config.py: {e}")
                # Try alternative method - direct file read
                try:
                    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Simple regex to find API key
                            import re
                            match = re.search(r'OPENAI_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
                            if match:
                                api_key = match.group(1).strip()
                                print(f"✓ API key loaded from config.py (alternative method)")
                except Exception as e2:
                    print(f"⚠ Alternative config loading also failed: {e2}")
        
        # If still not found, use placeholder
        if not api_key:
            api_key = "YOUR_LLM_API_KEY"  # Placeholder
    
    # Clean up API key - remove any whitespace
    if api_key:
        api_key = api_key.strip()
    
    if api_key == "YOUR_LLM_API_KEY" or api_key == "YOUR_OPENAI_API_KEY_HERE" or not api_key:
        return "Error: Please set your OpenAI API key. You can use one of these methods:\n" \
               "1. Set environment variable: export OPENAI_API_KEY='your-key-here' (Linux/Mac) or setx OPENAI_API_KEY 'your-key-here' (Windows)\n" \
               "2. Create config.py file in the same directory and set OPENAI_API_KEY = 'your-key-here'\n" \
               "3. Enter it when prompted by the script\n\n" \
               "Get your API key from:\n" \
               "  - OpenAI: https://platform.openai.com/api-keys\n" \
               "  - OpenRouter: https://openrouter.ai/keys (supports multiple AI models)"
    
    # Validate API key format (OpenAI keys start with 'sk-' or 'sk-or-v1-' for OpenRouter)
    if not (api_key.startswith('sk-') or api_key.startswith('sk-or-v1-')):
        return f"Error: Invalid API key format. API keys should start with 'sk-' or 'sk-or-v1-'. Your key starts with: '{api_key[:15]}...'"
    
    try:
        # Initialize OpenAI client with the cleaned API key
        print(f"Initializing OpenAI client...")
        
        # Check if this is an OpenRouter key (sk-or-v1-)
        if api_key.startswith('sk-or-v1-'):
            print("✓ Detected OpenRouter API key format")
            print("  Configuring client for OpenRouter...")
            
            # OpenRouter requires a different base URL
            # Also add recommended headers (HTTP-Referer and X-Title)
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/web-scraper",  # Optional: Your site URL
                    "X-Title": "Web Scraper AI Tool"  # Optional: Your app name
                }
            )
            print("  ✓ OpenRouter client configured successfully")
        else:
            # Standard OpenAI key
            print("✓ Using standard OpenAI API")
            client = openai.OpenAI(api_key=api_key)
        
        # Define the tool schema for function calling
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "scrape_section_by_heading",
                    "description": "Extract a section of content from a webpage by finding a heading that contains a keyword and returning all content under that heading until the next heading.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "heading_keyword": {
                                "type": "string",
                                "description": "A single keyword or short phrase that is likely to appear in an h2 or h3 heading on the webpage. This should be the most relevant term from the user's query that would identify the section they want. Examples: 'Gigafactories', 'Tesla', 'About Us', 'Pricing', 'Features'"
                            },
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to scrape"
                            }
                        },
                        "required": ["url", "heading_keyword"]
                    }
                }
            }
        ]
        
        # Create the user message
        user_message = f"User wants to extract information about: {topic_query}\n\n" \
                      f"Analyze this query and determine the single most appropriate heading keyword " \
                      f"that would be found in an h2 or h3 tag on the webpage at {url}. " \
                      f"Then call the scrape_section_by_heading function with this keyword."
        
        print(f"Analyzing topic query with AI: '{topic_query}'...")
        
        # Determine which model to use based on the API provider
        # For OpenRouter, we can use various models. Default to a cost-effective one.
        if api_key.startswith('sk-or-v1-'):
            # OpenRouter supports many models. Using a cost-effective one.
            # You can change this to: "openai/gpt-4o-mini", "anthropic/claude-3-haiku", etc.
            model = "openai/gpt-4o-mini"  # or "anthropic/claude-3-haiku", "google/gemini-pro", etc.
            print(f"  Using OpenRouter model: {model}")
        else:
            # Standard OpenAI model
            model = "gpt-4o-mini"
            print(f"  Using OpenAI model: {model}")
        
        # Call OpenAI/OpenRouter with function calling
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes user queries about web content and determines the best heading keyword to search for. You must always call the scrape_section_by_heading function with the most appropriate heading keyword."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            tools=tools,
            tool_choice="required"  # Force the model to use the function
        )
        
        # Extract the function call from the response
        message = response.choices[0].message
        
        if message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name == "scrape_section_by_heading":
                # Parse the function arguments
                function_args = json.loads(tool_call.function.arguments)
                heading_keyword = function_args.get("heading_keyword")
                function_url = function_args.get("url", url)
                
                print(f"AI determined heading keyword: '{heading_keyword}'")
                print(f"Extracting section from: {function_url}")
                
                # Call the actual scraping function
                result = scrape_section_by_heading(function_url, heading_keyword)
                return result
            else:
                return f"Error: Unexpected function call: {function_name}"
        else:
            return "Error: AI did not generate a function call. Please rephrase your query or check the API response."
    
    except openai.RateLimitError as e:
        error_msg = f"\n{'='*60}\n"
        error_msg += f"⚠ QUOTA/BILLING ISSUE - API Key is VALID but account has no credits!\n"
        error_msg += f"{'='*60}\n\n"
        error_msg += f"Your API key is working correctly, but:\n"
        error_msg += f"1. Your OpenAI account has exceeded its quota\n"
        error_msg += f"2. OR your account has no billing setup\n"
        error_msg += f"3. OR you've run out of credits\n\n"
        error_msg += f"Solutions:\n"
        error_msg += f"1. Check your billing: https://platform.openai.com/account/billing\n"
        error_msg += f"2. Add payment method: https://platform.openai.com/account/billing/payment-methods\n"
        error_msg += f"3. Check usage limits: https://platform.openai.com/account/limits\n"
        error_msg += f"4. Add credits to your account\n\n"
        error_msg += f"✅ Good News: Your API key is valid and loaded correctly!\n"
        error_msg += f"   You just need to add credits/billing to use it."
        return error_msg
    except openai.APIError as e:
        error_code = getattr(e, 'status_code', None)
        error_body = getattr(e, 'body', {})
        
        # Check for quota/insufficient_quota errors
        if error_code == 429 or (isinstance(error_body, dict) and error_body.get('error', {}).get('code') == 'insufficient_quota'):
            error_msg = f"\n{'='*60}\n"
            error_msg += f"⚠ QUOTA/BILLING ISSUE - API Key is VALID but account has no credits!\n"
            error_msg += f"{'='*60}\n\n"
            error_msg += f"Error Code: 429 (Insufficient Quota)\n\n"
            error_msg += f"Your API key is working correctly, but:\n"
            error_msg += f"1. Your OpenAI account has exceeded its quota\n"
            error_msg += f"2. OR your account has no billing setup\n"
            error_msg += f"3. OR you've run out of credits\n\n"
            error_msg += f"Solutions:\n"
            error_msg += f"1. Check your billing: https://platform.openai.com/account/billing\n"
            error_msg += f"2. Add payment method: https://platform.openai.com/account/billing/payment-methods\n"
            error_msg += f"3. Check usage limits: https://platform.openai.com/account/limits\n"
            error_msg += f"4. Add credits to your account\n\n"
            error_msg += f"✅ Good News: Your API key is valid and loaded correctly!\n"
            error_msg += f"   You just need to add credits/billing to use it."
            return error_msg
        else:
            return f"Error: OpenAI API error: {str(e)}\n\nIf this is an authentication error, please verify your API key is correct."
    except openai.AuthenticationError as e:
        error_msg = f"Error: Invalid API key. Please check your OpenAI API key.\n"
        error_msg += f"Details: {str(e)}\n"
        error_msg += f"API Key (first 10 chars): {api_key[:10]}...\n"
        error_msg += f"API Key length: {len(api_key)} characters\n"
        error_msg += f"\nTroubleshooting:\n"
        error_msg += f"1. Verify your API key at: https://platform.openai.com/api-keys\n"
        error_msg += f"2. Make sure there are no extra spaces or quotes in config.py\n"
        error_msg += f"3. Check that the key starts with 'sk-'\n"
        error_msg += f"4. Ensure your OpenAI account has credits/usage available"
        return error_msg
    except Exception as e:
        error_str = str(e)
        # Check if it's a quota error in the exception message
        if '429' in error_str or 'insufficient_quota' in error_str.lower() or 'quota' in error_str.lower():
            error_msg = f"\n{'='*60}\n"
            error_msg += f"⚠ QUOTA/BILLING ISSUE - API Key is VALID but account has no credits!\n"
            error_msg += f"{'='*60}\n\n"
            error_msg += f"Your API key is working correctly, but:\n"
            error_msg += f"1. Your OpenAI account has exceeded its quota\n"
            error_msg += f"2. OR your account has no billing setup\n"
            error_msg += f"3. OR you've run out of credits\n\n"
            error_msg += f"Solutions:\n"
            error_msg += f"1. Check your billing: https://platform.openai.com/account/billing\n"
            error_msg += f"2. Add payment method: https://platform.openai.com/account/billing/payment-methods\n"
            error_msg += f"3. Check usage limits: https://platform.openai.com/account/limits\n"
            error_msg += f"4. Add credits to your account\n\n"
            error_msg += f"✅ Good News: Your API key is valid and loaded correctly!\n"
            error_msg += f"   You just need to add credits/billing to use it."
            return error_msg
        else:
            return f"Error: An unexpected error occurred: {str(e)}\n\nAPI Key (first 10 chars): {api_key[:10]}..."


def ai_scrape_result_list(url: str, topic_query: str, api_key: Optional[str] = None) -> Union[List[Dict[str, str]], str]:
    """
    Use AI (OpenAI) to intelligently extract result lists from a webpage based on a natural language query.
    This is perfect for extracting results from sections like "Results", "Admit Cards", "Latest Jobs" etc.
    
    Args:
        url (str): The URL to scrape
        topic_query (str): Natural language query (e.g., "Extract all results from the Results section", "Get all job listings")
        api_key (Optional[str]): OpenAI API key. If None, will try to get from config.py or environment variable
        
    Returns:
        Union[List[Dict[str, str]], str]: List of result dictionaries or error message
    """
    if not OPENAI_AVAILABLE:
        return "Error: OpenAI library is not installed. Please install it with: pip install openai"
    
    # Get API key from config.py (same logic as ai_scrape_topic)
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            api_key = api_key.strip()
        
        if not api_key:
            try:
                import sys
                import importlib.util
                config_path = os.path.join(os.path.dirname(__file__), 'config.py')
                if os.path.exists(config_path):
                    spec = importlib.util.spec_from_file_location("config", config_path)
                    config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config)
                    if hasattr(config, 'OPENAI_API_KEY'):
                        loaded_key = config.OPENAI_API_KEY
                        if loaded_key and loaded_key != "YOUR_OPENAI_API_KEY_HERE" and loaded_key.strip():
                            api_key = loaded_key.strip()
                            print(f"✓ API key loaded from config.py (length: {len(api_key)})")
            except Exception as e:
                print(f"⚠ Error loading config.py: {e}")
                try:
                    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            import re
                            match = re.search(r'OPENAI_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
                            if match:
                                api_key = match.group(1).strip()
                                print(f"✓ API key loaded from config.py (alternative method)")
                except Exception as e2:
                    print(f"⚠ Alternative config loading also failed: {e2}")
        
        if not api_key:
            api_key = "YOUR_LLM_API_KEY"
    
    if api_key:
        api_key = api_key.strip()
    
    if api_key == "YOUR_LLM_API_KEY" or api_key == "YOUR_OPENAI_API_KEY_HERE" or not api_key:
        return "Error: Please set your OpenAI API key in config.py file. Get your API key from:\n" \
               "  - OpenAI: https://platform.openai.com/api-keys\n" \
               "  - OpenRouter: https://openrouter.ai/keys (supports multiple AI models)"
    
    if not (api_key.startswith('sk-') or api_key.startswith('sk-or-v1-')):
        return f"Error: Invalid API key format. API keys should start with 'sk-' or 'sk-or-v1-'. Your key starts with: '{api_key[:15]}...'"
    
    try:
        print(f"Initializing OpenAI client for result list extraction...")
        
        if api_key.startswith('sk-or-v1-'):
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/web-scraper",
                    "X-Title": "Web Scraper AI Tool"
                }
            )
            model = "openai/gpt-4o-mini"
        else:
            client = openai.OpenAI(api_key=api_key)
            model = "gpt-4o-mini"
        
        # Define the tool schema for function calling - support both section extraction and result list extraction
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "scrape_result_list",
                    "description": "Extract a list of results from a webpage by finding a section (like 'Results', 'Admit Cards', 'Latest Jobs') and returning all list items from that section. Each result should have a title, link, and optionally a status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "section_name": {
                                "type": "string",
                                "description": "The name of the section to extract results from. Examples: 'Results', 'Admit Cards', 'Latest Jobs', 'Notifications'. This should match the heading or title of the section on the webpage."
                            },
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to scrape"
                            }
                        },
                        "required": ["url", "section_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_section_by_heading",
                    "description": "Extract a section of content from a webpage by finding a heading that contains a keyword and returning all content under that heading until the next heading.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "heading_keyword": {
                                "type": "string",
                                "description": "A single keyword or short phrase that is likely to appear in an h2 or h3 heading on the webpage."
                            },
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to scrape"
                            }
                        },
                        "required": ["url", "heading_keyword"]
                    }
                }
            }
        ]
        
        user_message = f"User wants to extract result list from: {topic_query}\n\n" \
                      f"Analyze this query and determine the best section name (like 'Results', 'Admit Cards', 'Latest Jobs') " \
                      f"that would be found on the webpage at {url}. " \
                      f"If the query is about extracting a list of results, jobs, admit cards, or similar structured data, " \
                      f"use the scrape_result_list function. Otherwise, use scrape_section_by_heading function."
        
        print(f"Analyzing topic query with AI: '{topic_query}'...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes user queries about web content and determines the best method to extract data. For queries about result lists, jobs, admit cards, or similar structured list data, use scrape_result_list. For other content extraction, use scrape_section_by_heading."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            tools=tools,
            tool_choice="required"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name == "scrape_result_list":
                function_args = json.loads(tool_call.function.arguments)
                section_name = function_args.get("section_name")
                function_url = function_args.get("url", url)
                
                print(f"AI determined section name: '{section_name}'")
                print(f"Extracting result list from: {function_url}")
                
                result = scrape_result_list(function_url, section_name, None)
                return result
            elif function_name == "scrape_section_by_heading":
                function_args = json.loads(tool_call.function.arguments)
                heading_keyword = function_args.get("heading_keyword")
                function_url = function_args.get("url", url)
                
                print(f"AI determined heading keyword: '{heading_keyword}'")
                print(f"Extracting section from: {function_url}")
                
                result = scrape_section_by_heading(function_url, heading_keyword)
                # Convert text result to list format for consistency
                if isinstance(result, str) and not result.startswith('Error:') and not result.startswith('Not found'):
                    return [{'title': heading_keyword, 'text': result, 'link': '', 'status': ''}]
                return result
            else:
                return f"Error: Unexpected function call: {function_name}"
        else:
            return "Error: AI did not generate a function call. Please rephrase your query or check the API response."
    
    except Exception as e:
        error_str = str(e)
        if '429' in error_str or 'insufficient_quota' in error_str.lower() or 'quota' in error_str.lower():
            return ("Error: API quota exceeded or no credits available. Please check your OpenAI/OpenRouter account billing.")
        else:
            return f"Error: An unexpected error occurred: {str(e)}"


def scrape_result_list(url: str, section_name: Optional[str] = None, list_selector: Optional[str] = None) -> Union[List[Dict[str, str]], str]:
    """
    Extract result items from list-based sections (like "Results", "Admit Cards", "Latest Jobs").
    This is specifically designed for websites like Sarkari Result that display results as list items.
    
    Args:
        url (str): The URL to scrape
        section_name (Optional[str]): Name of the section to extract (e.g., "Results", "Admit Cards"). 
                                      If None, will try to find and extract all result sections.
        list_selector (Optional[str]): CSS selector for the list container or list items. 
                                       If None, will auto-detect based on section name.
        
    Returns:
        Union[List[Dict[str, str]], str]: List of result dictionaries or error message
    """
    soup = get_page_content(url)
    if not soup:
        return "Error: Could not fetch the webpage"
    
    def normalize_url(link_url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not link_url:
            return ""
        if link_url.startswith('//'):
            return 'https:' + link_url
        elif link_url.startswith('http://') or link_url.startswith('https://'):
            return link_url
        elif link_url.startswith('/'):
            return urljoin(base_url, link_url)
        elif link_url.startswith('#'):
            return base_url + link_url
        else:
            return urljoin(base_url, link_url)
    
    def extract_result_item(item_element) -> Dict[str, str]:
        """Extract data from a single result list item."""
        result_data = {
            'title': '',
            'link': '',
            'text': '',
            'status': ''
        }
        
        # Try to find a link in the item
        link_elem = item_element.find('a', href=True)
        
        if link_elem:
            # Extract link
            result_data['link'] = normalize_url(link_elem.get('href'), url)
            # Extract title/text from link
            link_text = link_elem.get_text(strip=True)
            if link_text:
                result_data['title'] = link_text
                result_data['text'] = link_text
        elif item_element.name == 'a' and item_element.get('href'):
            # The item itself is a link
            result_data['link'] = normalize_url(item_element.get('href'), url)
            link_text = item_element.get_text(strip=True)
            if link_text:
                result_data['title'] = link_text
                result_data['text'] = link_text
        else:
            # No link found, just extract text
            text = item_element.get_text(strip=True)
            if text:
                result_data['title'] = text
                result_data['text'] = text
        
        # Try to extract status (like "Out", "Final Result", "Start", etc.)
        if result_data['text']:
            # Look for common status indicators
            status_patterns = [
                r'\s*-\s*(Out|Final Result|Start|Last Date|Date Extend|Reminder|Booking)',
                r'\((.*?)\)$',  # Text in parentheses at the end
            ]
            for pattern in status_patterns:
                match = re.search(pattern, result_data['text'], re.IGNORECASE)
                if match:
                    result_data['status'] = match.group(1) if match.lastindex else match.group(0)
                    break
        
        return result_data
    
    results = []
    
    # If a specific selector is provided, use it
    if list_selector:
        items = soup.select(list_selector)
        if items:
            print(f"Found {len(items)} items using selector: {list_selector}")
            for idx, item in enumerate(items, 1):
                result_data = extract_result_item(item)
                if result_data['title'] or result_data['text']:
                    result_data['index'] = idx
                    results.append(result_data)
            return results if results else "Found elements but could not extract data from them."
    
    # If section name is provided, find that section
    if section_name:
        section_name_lower = section_name.lower()
        
        # Try multiple methods to find the section
        # Method 1: Find by heading text (h1-h6, div, span with text matching)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'strong', 'b', 'p'])
        target_section = None
        target_list = None
        
        for heading in headings:
            heading_text = heading.get_text(strip=True).lower()
            if section_name_lower in heading_text and len(heading_text) < 50:  # Reasonable heading length
                # Found the section heading, now find the list container
                # Method 1a: Check if heading's parent or next sibling has a list
                current = heading
                for _ in range(5):  # Go up/down max 5 levels
                    # Check parent
                    if current.parent:
                        parent = current.parent
                        # Look for ul/ol directly in parent
                        list_container = parent.find(['ul', 'ol'])
                        if list_container:
                            list_items = list_container.find_all('li', recursive=False)
                            if list_items and len(list_items) >= 2:
                                target_list = list_container
                                print(f"Found section '{section_name}' with {len(list_items)} items (method: parent list)")
                                break
                        
                        # Check next siblings for lists
                        for sibling in parent.find_all_next(['ul', 'ol'], limit=3):
                            list_items = sibling.find_all('li', recursive=False)
                            if list_items and len(list_items) >= 2:
                                # Make sure we're not going too far (check if heading is nearby)
                                if sibling.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) == heading:
                                    target_list = sibling
                                    print(f"Found section '{section_name}' with {len(list_items)} items (method: sibling list)")
                                    break
                        if target_list:
                            break
                    
                    # Check if current element itself contains a list
                    list_container = current.find(['ul', 'ol'])
                    if list_container:
                        list_items = list_container.find_all('li', recursive=False)
                        if list_items and len(list_items) >= 2:
                            target_list = list_container
                            print(f"Found section '{section_name}' with {len(list_items)} items (method: embedded list)")
                            break
                    
                    if current.parent:
                        current = current.parent
                    else:
                        break
                
                if target_list:
                    break
        
        # Method 2: Find by class/id containing section name
        if not target_list:
            section_selectors = [
                f'[class*="{section_name_lower}"]',
                f'[id*="{section_name_lower}"]',
                f'.{section_name_lower}',
                f'#{section_name_lower}'
            ]
            for selector in section_selectors:
                try:
                    sections = soup.select(selector)
                    for section in sections:
                        list_container = section.find(['ul', 'ol'])
                        if list_container:
                            list_items = list_container.find_all('li', recursive=False)
                            if list_items and len(list_items) >= 2:
                                target_list = list_container
                                print(f"Found section '{section_name}' with {len(list_items)} items (method: class/id selector)")
                                break
                    if target_list:
                        break
                except:
                    continue
        
        if target_list:
            # Extract all list items from the found list
            list_items = target_list.find_all('li', recursive=False)
            if not list_items:
                list_items = target_list.find_all('li', recursive=True)
            
            for idx, item in enumerate(list_items, 1):
                result_data = extract_result_item(item)
                if result_data['title'] or result_data['text']:
                    result_data['index'] = idx
                    results.append(result_data)
            
            if results:
                return results
    
    # Auto-detect: Try to find common result list patterns
    # Method 1: Find all ul/ol lists and check if they contain result-like items
    all_lists = soup.find_all(['ul', 'ol'])
    candidate_lists = []
    
    for list_elem in all_lists:
        list_items = list_elem.find_all('li', recursive=False)
        if len(list_items) >= 3:  # At least 3 items to be considered a result list
            # Check if items have links (common in result lists)
            links_count = sum(1 for li in list_items if li.find('a', href=True))
            link_ratio = links_count / len(list_items) if list_items else 0
            
            # Check if list items contain result-like keywords
            result_keywords = ['result', 'admit', 'card', 'exam', 'job', 'notification', 'form', 'out', 'start']
            keyword_matches = 0
            for li in list_items[:5]:  # Check first 5 items
                li_text = li.get_text(strip=True).lower()
                if any(keyword in li_text for keyword in result_keywords):
                    keyword_matches += 1
            
            # Score the list based on criteria
            score = 0
            if link_ratio >= 0.7:
                score += 3
            elif link_ratio >= 0.5:
                score += 2
            if keyword_matches >= 3:
                score += 2
            elif keyword_matches >= 2:
                score += 1
            if len(list_items) >= 10:
                score += 1
            
            if score >= 3:  # Good candidate
                candidate_lists.append((list_elem, list_items, score))
    
    # Sort by score and use the best candidate
    if candidate_lists:
        candidate_lists.sort(key=lambda x: x[2], reverse=True)
        best_list, list_items, score = candidate_lists[0]
        print(f"Auto-detected result list with {len(list_items)} items (score: {score})")
        for idx, item in enumerate(list_items, 1):
            result_data = extract_result_item(item)
            if result_data['title'] or result_data['text']:
                result_data['index'] = idx
                results.append(result_data)
        if results:
            return results
    
    # Method 2: Find sections with headings containing "result", "admit", "job", etc.
    section_keywords = ['result', 'admit', 'job', 'notification', 'exam', 'recruitment']
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'span'], 
                            class_=re.compile(r'title|heading|header', re.I))
    
    for heading in headings:
        heading_text = heading.get_text(strip=True).lower()
        if any(keyword in heading_text for keyword in section_keywords):
            # Find nearby list
            parent = heading.parent
            for _ in range(4):
                if parent:
                    list_items = parent.find_all(['li', 'a'], recursive=False)
                    if not list_items:
                        list_container = parent.find(['ul', 'ol'])
                        if list_container:
                            list_items = list_container.find_all('li', recursive=False)
                    
                    if list_items and len(list_items) >= 3:
                        print(f"Found result section near heading: {heading.get_text(strip=True)}")
                        for idx, item in enumerate(list_items, 1):
                            result_data = extract_result_item(item)
                            if result_data['title'] or result_data['text']:
                                result_data['index'] = idx
                                results.append(result_data)
                        if results:
                            return results
                    parent = parent.parent if parent.parent else None
    
    if not results:
        return ("No result lists found. Try:\n"
                "1. Specify a section name (e.g., 'Results', 'Admit Cards')\n"
                "2. Specify a CSS selector for list items (e.g., 'ul li', '.result-list li')")
    
    return results


def scrape_card_results(url: str, card_selector: Optional[str] = None) -> Union[List[Dict[str, str]], str]:
    """
    Extract structured data from card-based results on a webpage.
    Each card typically contains: title, description, image, and link.
    
    Args:
        url (str): The URL to scrape
        card_selector (Optional[str]): CSS selector for card elements. If None, will try common selectors.
        
    Returns:
        Union[List[Dict[str, str]], str]: List of card dictionaries or error message
    """
    soup = get_page_content(url)
    if not soup:
        return "Error: Could not fetch the webpage"
    
    def normalize_url(link_url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if not link_url:
            return ""
        if link_url.startswith('//'):
            return 'https:' + link_url
        elif link_url.startswith('http://') or link_url.startswith('https://'):
            return link_url
        elif link_url.startswith('/'):
            return urljoin(base_url, link_url)
        elif link_url.startswith('#'):
            return base_url + link_url
        else:
            return urljoin(base_url, link_url)
    
    def normalize_image_url(img_url: str, base_url: str) -> str:
        """Convert relative image URLs to absolute URLs."""
        if not img_url:
            return ""
        if img_url.startswith('//'):
            return 'https:' + img_url
        elif img_url.startswith('http://') or img_url.startswith('https://'):
            return img_url
        elif img_url.startswith('/'):
            return urljoin(base_url, img_url)
        else:
            return urljoin(base_url, img_url)
    
    def extract_card_data(card_element) -> Dict[str, str]:
        """Extract structured data from a single card element."""
        card_data = {
            'title': '',
            'description': '',
            'image': '',
            'link': '',
            'text': ''
        }
        
        # Extract title (try common title selectors)
        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="name"]', '.card-title', '.result-title']
        for selector in title_selectors:
            title_elem = card_element.select_one(selector)
            if title_elem:
                card_data['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract link (from anchor tag or card itself)
        link_elem = card_element.find('a', href=True)
        if link_elem:
            card_data['link'] = normalize_url(link_elem.get('href'), url)
        elif card_element.name == 'a' and card_element.get('href'):
            card_data['link'] = normalize_url(card_element.get('href'), url)
        
        # Extract image
        img_elem = card_element.find('img')
        if img_elem:
            img_url = (img_elem.get('src') or 
                      img_elem.get('data-src') or 
                      img_elem.get('data-lazy-src') or
                      img_elem.get('data-original') or
                      img_elem.get('data-url'))
            if img_url:
                card_data['image'] = normalize_image_url(img_url, url)
        
        # Extract description/text (try common description selectors)
        desc_selectors = ['.description', '.desc', '[class*="desc"]', 'p', '.text', '[class*="text"]', '.summary', '[class*="summary"]']
        for selector in desc_selectors:
            desc_elem = card_element.select_one(selector)
            if desc_elem and desc_elem.get_text(strip=True):
                card_data['description'] = desc_elem.get_text(strip=True)
                break
        
        # If no description found, get all text content (excluding title)
        if not card_data['description']:
            # Get all text from the card
            all_text = card_element.get_text(separator=' ', strip=True)
            # Remove the title from the text if we found one
            if card_data['title']:
                all_text = all_text.replace(card_data['title'], '', 1).strip()
            # Clean up extra whitespace
            text_words = all_text.split()
            if text_words:
                card_data['description'] = ' '.join(text_words[:50])  # First 50 words
                card_data['text'] = ' '.join(text_words)
            else:
                card_data['text'] = all_text
        else:
            card_data['text'] = card_data['description']
        
        # If no title found, try to get it from link text or first heading
        if not card_data['title']:
            if link_elem:
                card_data['title'] = link_elem.get_text(strip=True)
            else:
                # Get first significant text
                first_text = card_element.get_text(strip=True).split('\n')[0].strip()
                if first_text and len(first_text) < 100:
                    card_data['title'] = first_text[:100]
        
        return card_data
    
    # Try to find cards using provided selector or common selectors
    card_elements = []
    
    if card_selector:
        card_elements = soup.select(card_selector)
    else:
        # Try common card selectors
        common_selectors = [
            '.card',
            '.result-card',
            '.item-card',
            '.card-item',
            '[class*="card"]',
            '.result-item',
            '.item',
            '[class*="result"]',
            '.product-card',
            '.product-item',
            '[data-testid*="card"]',
            '[class*="grid-item"]',
            '.search-result',
            '[class*="search-result"]',
            'article',
            '[role="article"]'
        ]
        
        for selector in common_selectors:
            card_elements = soup.select(selector)
            if card_elements:
                print(f"Found {len(card_elements)} cards using selector: {selector}")
                break
    
    if not card_elements:
        return "No cards found. Try specifying a custom CSS selector for the card elements."
    
    # Extract data from each card
    cards_data = []
    for idx, card in enumerate(card_elements, 1):
        card_data = extract_card_data(card)
        card_data['index'] = idx
        # Only add cards with at least some content
        if card_data['title'] or card_data['description'] or card_data['link']:
            cards_data.append(card_data)
    
    if not cards_data:
        return "Found card elements but could not extract data from them."
    
    return cards_data


def print_result(data_type: str, result: Union[str, List[str], None]):
    """
    Print the extracted result in a clean format.
    
    Args:
        data_type (str): Type of data extracted
        result: The extracted data
    """
    print("\n" + "="*60)
    print(f"EXTRACTED {data_type.upper()}:")
    print("="*60)
    
    if result is None:
        print("Error: Could not extract data")
    elif isinstance(result, list):
        if len(result) == 1:
            print(result[0])
        else:
            for i, item in enumerate(result, 1):
                print(f"{i}. {item}")
    else:
        print(result)
    
    print("="*60 + "\n")


def print_result_list(results: Union[List[Dict[str, str]], str]):
    """
    Print result list in a formatted way.
    
    Args:
        results: List of result dictionaries or error message
    """
    print("\n" + "="*60)
    print("EXTRACTED RESULT LIST:")
    print("="*60)
    
    if isinstance(results, str):
        print(results)
    elif isinstance(results, list):
        print(f"\nFound {len(results)} result(s):\n")
        for result in results:
            idx = result.get('index', '?')
            title = result.get('title', result.get('text', ''))
            link = result.get('link', '')
            status = result.get('status', '')
            
            print(f"{idx}. {title}")
            if status:
                print(f"   Status: {status}")
            if link:
                print(f"   Link: {link}")
            print()
    else:
        print("Error: Invalid result data format")
    
    print("="*60 + "\n")


def print_card_results(cards: Union[List[Dict[str, str]], str]):
    """
    Print card results in a formatted way.
    
    Args:
        cards: List of card dictionaries or error message
    """
    print("\n" + "="*60)
    print("EXTRACTED CARD RESULTS:")
    print("="*60)
    
    if isinstance(cards, str):
        print(cards)
    elif isinstance(cards, list):
        print(f"\nFound {len(cards)} card(s):\n")
        for card in cards:
            print(f"Card #{card.get('index', '?')}:")
            if card.get('title'):
                print(f"  Title: {card['title']}")
            if card.get('description'):
                print(f"  Description: {card['description'][:100]}..." if len(card['description']) > 100 else f"  Description: {card['description']}")
            if card.get('link'):
                print(f"  Link: {card['link']}")
            if card.get('image'):
                print(f"  Image: {card['image']}")
            print()
    else:
        print("Error: Invalid card data format")
    
    print("="*60 + "\n")


def main():
    """
    Interactive main function that prompts user for URL and extraction options.
    """
    print("\n" + "="*60)
    print("WEB SCRAPER - Interactive Mode")
    print("="*60)
    
    # Get URL from user
    url = input("\nEnter the URL to scrape: ").strip()
    if not url:
        print("Error: URL cannot be empty!")
        return
    
    # Add https:// if not present
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    # Ask what to extract
    print("\nWhat would you like to extract?")
    print("1. Text")
    print("2. Image")
    print("3. Link")
    print("4. All (Text, Image, and Link)")
    print("5. Card Results (extract structured data from card-based layouts)")
    print("6. Result List (extract results from list-based sections like 'Results', 'Admit Cards')")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    # Handle Text extraction
    if choice == '1':
        print("\nHow would you like to search for text?")
        print("1. Search by keyword (e.g., 'about us', 'notice', 'alert')")
        print("2. Use CSS selector")
        print("3. Get default text (first heading)")
        print("4. Search by AI Topic Query (e.g., 'Tesla Gigafactories', 'latest news about AI')")
        
        text_choice = input("\nEnter your choice (1-4): ").strip()
        
        if text_choice == '1':
            keyword = input("\nEnter the keyword to search for: ").strip()
            if keyword:
                result = search_text_by_keyword(url, keyword)
                print_result('text', result)
            else:
                print("Error: Keyword cannot be empty!")
        
        elif text_choice == '2':
            selector = input("Enter CSS selector (e.g., 'h1.title', '.product-title'): ").strip()
            result = scrape_text_with_selector(url, selector if selector else None)
            print_result('text', result)
        
        elif text_choice == '3':
            result = scrape_text_with_selector(url, None)
            print_result('text', result)
        
        elif text_choice == '4':
            if not OPENAI_AVAILABLE:
                print("\nError: OpenAI library is not installed.")
                print("Please install it with: pip install openai")
                print("Then set your API key as an environment variable: export OPENAI_API_KEY='your-key-here'")
            else:
                topic_query = input("\nEnter your topic query (e.g., 'Summarize the latest developments on Tesla's Gigafactories'): ").strip()
                if topic_query:
                    # Check for API key in environment or ask user
                    api_key = os.getenv('OPENAI_API_KEY')
                    if not api_key:
                        use_custom_key = input("OpenAI API key not found in environment. Enter API key now? (y/n): ").strip().lower()
                        if use_custom_key == 'y':
                            api_key = input("Enter your OpenAI API key: ").strip()
                        else:
                            api_key = None
                    
                    result = ai_scrape_topic(url, topic_query, api_key)
                    print_result('text', result)
                else:
                    print("Error: Topic query cannot be empty!")
        
        else:
            print("Invalid choice!")
    
    # Handle Image extraction
    elif choice == '2':
        print("\nHow would you like to search for images?")
        print("1. Search by keyword (e.g., 'logo', 'product', 'banner')")
        print("2. List all images and select by number")
        print("3. Use CSS selector")
        print("4. Get default image (first main image)")
        
        image_choice = input("\nEnter your choice (1-4): ").strip()
        
        if image_choice == '1':
            keyword = input("\nEnter the keyword to search for: ").strip()
            if keyword:
                result = search_image_by_keyword(url, keyword)
                print_result('image', result)
            else:
                print("Error: Keyword cannot be empty!")
        
        elif image_choice == '2':
            print("\nFetching all images from the page...")
            images = list_all_images(url)
            
            if images:
                print(f"\nFound {len(images)} image(s):\n")
                for img in images:
                    print(f"{img['index']}. Alt: {img['alt'][:50]}...")
                    print(f"   Title: {img['title'][:50]}...")
                    print(f"   URL: {img['url'][:80]}...")
                    print()
                
                selection = input(f"Enter the image number (1-{len(images)}) or 'all' for all images: ").strip()
                
                if selection.lower() == 'all':
                    result = [img['url'] for img in images]
                    print_result('image', result)
                else:
                    try:
                        img_num = int(selection)
                        if 1 <= img_num <= len(images):
                            result = images[img_num - 1]['url']
                            print_result('image', result)
                        else:
                            print(f"Error: Please enter a number between 1 and {len(images)}")
                    except ValueError:
                        print("Error: Please enter a valid number or 'all'")
            else:
                print("No images found on the page.")
        
        elif image_choice == '3':
            selector = input("Enter CSS selector (e.g., '.product-image img', '#main-img'): ").strip()
            result = scrape_image_with_selector(url, selector if selector else None)
            print_result('image', result)
        
        elif image_choice == '4':
            result = scrape_image_with_selector(url, None)
            print_result('image', result)
        
        else:
            print("Invalid choice!")
    
    # Handle Link extraction
    elif choice == '3':
        print("\nHow would you like to search for links?")
        print("1. Search by keyword (e.g., 'contact', 'buy', 'cart')")
        print("2. Use CSS selector")
        print("3. Get default link (first link)")
        
        link_choice = input("\nEnter your choice (1-3): ").strip()
        
        if link_choice == '1':
            keyword = input("\nEnter the keyword to search for: ").strip()
            if keyword:
                result = search_link_by_keyword(url, keyword)
                print_result('link', result)
            else:
                print("Error: Keyword cannot be empty!")
        
        elif link_choice == '2':
            selector = input("Enter CSS selector (e.g., 'a.button', '#buy-now'): ").strip()
            result = scrape_link_with_selector(url, selector if selector else None)
            print_result('link', result)
        
        elif link_choice == '3':
            result = scrape_link_with_selector(url, None)
            print_result('link', result)
        
        else:
            print("Invalid choice!")
    
    # Handle All extraction
    elif choice == '4':
        print("\nExtracting all data types...")
        
        # Text
        print("\n--- TEXT EXTRACTION ---")
        text_keyword = input("Enter keyword to search for text (or press Enter for default): ").strip()
        if text_keyword:
            text_result = search_text_by_keyword(url, text_keyword)
        else:
            text_result = scrape_text_with_selector(url, None)
        
        # Image
        print("\n--- IMAGE EXTRACTION ---")
        image_keyword = input("Enter keyword to search for image (or press Enter for default): ").strip()
        if image_keyword:
            image_result = search_image_by_keyword(url, image_keyword)
        else:
            image_result = scrape_image_with_selector(url, None)
        
        # Link
        print("\n--- LINK EXTRACTION ---")
        link_keyword = input("Enter keyword to search for link (or press Enter for default): ").strip()
        if link_keyword:
            link_result = search_link_by_keyword(url, link_keyword)
        else:
            link_result = scrape_link_with_selector(url, None)
        
        # Display results
        print("\n" + "="*60)
        print("EXTRACTED DATA:")
        print("="*60)
        print(f"\nTEXT:")
        if isinstance(text_result, list):
            for i, item in enumerate(text_result, 1):
                print(f"  {i}. {item}")
        else:
            print(f"  {text_result}")
        
        print(f"\nIMAGE:")
        if isinstance(image_result, list):
            for i, item in enumerate(image_result, 1):
                print(f"  {i}. {item}")
        else:
            print(f"  {image_result}")
        
        print(f"\nLINK:")
        if isinstance(link_result, list):
            for i, item in enumerate(link_result, 1):
                print(f"  {i}. {item}")
        else:
            print(f"  {link_result}")
        print("="*60 + "\n")
    
    # Handle Card Results extraction
    elif choice == '5':
        print("\nExtracting card-based results...")
        print("The script will automatically detect card elements on the page.")
        print("If no cards are found, you can specify a custom CSS selector.")
        
        use_custom = input("\nDo you want to specify a custom CSS selector for cards? (y/n): ").strip().lower()
        card_selector = None
        
        if use_custom == 'y':
            card_selector = input("Enter CSS selector for card elements (e.g., '.card', '.result-item', '#results .item'): ").strip()
            if not card_selector:
                card_selector = None
                print("No selector provided, using automatic detection...")
        
        result = scrape_card_results(url, card_selector)
        print_card_results(result)
        
        # Option to save results to JSON
        if isinstance(result, list) and len(result) > 0:
            save_json = input("\nDo you want to save the results to a JSON file? (y/n): ").strip().lower()
            if save_json == 'y':
                filename = input("Enter filename (without extension, default: card_results): ").strip()
                if not filename:
                    filename = "card_results"
                if not filename.endswith('.json'):
                    filename += '.json'
                
                try:
                    # Convert to JSON-serializable format
                    json_data = []
                    for card in result:
                        json_card = dict(card)  # Create a copy of the card dictionary
                        json_data.append(json_card)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"✓ Results saved to {filename}")
                except Exception as e:
                    print(f"Error saving file: {e}")
    
    # Handle Result List extraction
    elif choice == '6':
        print("\nExtracting result list from list-based sections...")
        print("This is perfect for websites like Sarkari Result that show results as lists.")
        
        use_section = input("\nDo you want to extract a specific section? (y/n): ").strip().lower()
        section_name = None
        list_selector = None
        
        if use_section == 'y':
            section_name = input("Enter section name (e.g., 'Results', 'Admit Cards', 'Latest Jobs'): ").strip()
            if not section_name:
                section_name = None
                print("No section name provided, will try auto-detection...")
        else:
            use_selector = input("Do you want to specify a CSS selector for list items? (y/n): ").strip().lower()
            if use_selector == 'y':
                list_selector = input("Enter CSS selector (e.g., 'ul li', '.result-list li', '#results li'): ").strip()
                if not list_selector:
                    list_selector = None
                    print("No selector provided, using auto-detection...")
        
        result = scrape_result_list(url, section_name, list_selector)
        print_result_list(result)
        
        # Option to save results to JSON
        if isinstance(result, list) and len(result) > 0:
            save_json = input("\nDo you want to save the results to a JSON file? (y/n): ").strip().lower()
            if save_json == 'y':
                filename = input("Enter filename (without extension, default: result_list): ").strip()
                if not filename:
                    filename = "result_list"
                if not filename.endswith('.json'):
                    filename += '.json'
                
                try:
                    # Convert to JSON-serializable format
                    json_data = []
                    for item in result:
                        json_item = dict(item)
                        json_data.append(json_item)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"✓ Results saved to {filename}")
                except Exception as e:
                    print(f"Error saving file: {e}")
    
    else:
        print("Invalid choice! Please run the script again and select 1-6.")


if __name__ == "__main__":
    main()
