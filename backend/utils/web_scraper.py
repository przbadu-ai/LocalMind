"""Web scraping utility with fallback."""

import logging
from typing import Optional

import requests
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_and_extract(url: str) -> str:
    """Fetch URL and extract main content as Markdown.
    
    Tries trafilatura first for clean extraction.
    Falls back to raw requests + BeautifulSoup if trafilatura fails.
    """
    logger.info(f"Fetching URL: {url}")
    
    # Method 1: Trafilatura (Best for articles/content)
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            if result:
                logger.info("Successfully extracted content with trafilatura")
                return result
            else:
                logger.warning("Trafilatura result was empty")
        else:
            logger.warning("Trafilatura failed to download URL")
            
    except Exception as e:
        logger.error(f"Trafilatura error: {e}")

    # Method 2: Fallback to requests + BeautifulSoup (Raw text)
    logger.info("Falling back to requests + BeautifulSoup")
    try:
        response = requests.get(
            url, 
            headers={"User-Agent": USER_AGENT}, 
            timeout=15
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return f"**[Fallback Extraction]**\n\n{text[:10000]}..." if len(text) > 10000 else text
        
    except Exception as e:
        logger.error(f"Fallback scraping error: {e}")
        return f"Error fetching URL: {str(e)}"
