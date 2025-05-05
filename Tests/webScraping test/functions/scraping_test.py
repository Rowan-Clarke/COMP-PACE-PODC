import pandas as pd
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
import os
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import magic
import mimetypes
import io
from functools import lru_cache
from ratelimit import limits, sleep_and_retry
from contextlib import asynccontextmanager
import time
import re
import ssl
import tempfile
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting configuration
CALLS_PER_SECOND = 2
PERIOD = 1

class WebScraper:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.driver: Optional[webdriver.Chrome] = None
        # Update downloads directory path
        self.downloads_dir = Path("Tests/webScraping test/data/Downloads")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp())

    async def __aenter__(self):
        # Initialize resources with SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Configure download behavior
        chrome_options.add_experimental_option('prefs', {
            'download.default_directory': str(self.downloads_dir.absolute()),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True,
            'safebrowsing.enabled': True
        })
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup resources
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @lru_cache(maxsize=100)
    def get_robots_parser(self, domain: str) -> RobotFileParser:
        """Cache robots.txt parsers for domains"""
        parser = RobotFileParser()
        parser.set_url(f"{domain}/robots.txt")
        try:
            parser.read()
        except Exception as e:
            logger.error(f"Error reading robots.txt for {domain}: {e}")
        return parser

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=PERIOD)
    async def fetch_url(self, url: str, headers: Dict[str, str]) -> Optional[bytes]:
        """Rate-limited URL fetching"""
        try:
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    return await response.read()
                logger.warning(f"Failed to fetch {url}: Status {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def scrape_pdf(self, url: str, title: str) -> Dict[str, Any]:
        """Enhanced PDF scraping with download handling"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
            'Connection': 'keep-alive'
        }
        
        try:
            # First try direct aiohttp download
            async with self.session.get(url, headers=headers, timeout=60) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Check if it's a PDF
                    if content.startswith(b'%PDF'):
                        return await self._process_pdf_content(content, title)
                
                # If not successful, try with requests and Selenium
                return await self._try_alternative_pdf_download(url, title)
                    
        except Exception as e:
            logger.error(f"Error in primary PDF fetch for {url}: {str(e)}")
            return await self._try_alternative_pdf_download(url, title)

    async def _try_alternative_pdf_download(self, url: str, title: str) -> Dict[str, Any]:
        """Try alternative methods to get PDF content"""
        try:
            # Try using requests first
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                content = response.content
                if content.startswith(b'%PDF'):
                    return await self._process_pdf_content(content, title)
            
            # If requests fails, try Selenium
            self.driver.get(url)
            await asyncio.sleep(3)  # Wait for potential download
            
            # Check downloads directory using class property
            pdf_files = list(self.downloads_dir.glob("*.pdf"))
            
            # Sort by modification time to get the most recent
            if pdf_files:
                newest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
                # Only process if modified in last 10 seconds
                if time.time() - newest_pdf.stat().st_mtime < 10:
                    # Copy to temp directory
                    temp_pdf = self.temp_dir / newest_pdf.name
                    shutil.copy2(newest_pdf, temp_pdf)
                    
                    # Read and process PDF
                    with open(temp_pdf, 'rb') as f:
                        return await self._process_pdf_content(f.read(), title)
            
            return self._create_error_response(title, "Failed to download PDF")
            
        except Exception as e:
            logger.error(f"Error in alternative PDF download for {url}: {str(e)}")
            return self._create_error_response(title, str(e))

    async def _process_pdf_content(self, content: bytes, title: str) -> Dict[str, Any]:
        """Process PDF content and extract text"""
        try:
            pdf_content = io.BytesIO(content)
            reader = PdfReader(pdf_content)
            
            text_content = []
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text_content.append(extracted_text.strip())
            
            if not text_content:
                return self._create_error_response(title, "No text content extracted")
            
            return {
                "Title": title,
                "Content": "\n".join(text_content)[:5000],
                "Accessible": True,
                "Type": "PDF"
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF content for {title}: {str(e)}")
            return self._create_error_response(title, f"PDF processing error: {str(e)}")

    async def scrape_html(self, url: str, title: str) -> Dict[str, str]:
        try:
            # Set a proper referrer and cookies
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/'
                }
            })
            
            self.driver.set_page_load_timeout(30)
            self.driver.get(url)
            await asyncio.sleep(3)
            
            # Check for 404 or error pages
            if any(error_text in self.driver.page_source.lower() for error_text in 
                ['404', 'not found', 'página', 'error', 'no hemos podido']):
                return self._create_error_response(title, "Page not found (404)")
            
            # Extract content using improved selectors
            content_selectors = [
                "#main-content",
                "main article",
                "article",
                ".content-area",
                ".entry-content",
                "[role='main']",
                "#content",
                ".main",
                "content-type-content"
            ]
            
            content = None
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements("css selector", selector)
                    if elements:
                        content = ' '.join(elem.text for elem in elements if elem.text)
                        if len(content) > 150:  # Minimum content length
                            break
                except Exception:
                    continue
            
            if not content:
                try:
                    content = self.driver.find_element("tag name", "body").text
                except Exception:
                    return self._create_error_response(title, "No content found")
            
            # Clean content
            content = ' '.join(content.split())
            content = re.sub(r'\s+', ' ', content)
            
            if len(content) < 150:
                return self._create_error_response(title, "Insufficient content found")
            
            return {
                "Title": title,
                "Content": content[:5000],
                "Accessible": True,
                "Type": "HTML"
            }
                
        except Exception as e:
            logger.error(f"Error scraping HTML {url}: {e}")
            return self._create_error_response(title, str(e))

    def _create_error_response(self, title: str, error: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "Title": title,
            "Content": f"Error: {error}",
            "Accessible": False,
            "Type": "Unknown"
        }

    @staticmethod
    def detect_website_type(url: str) -> str:
        """Detect website type from URL"""
        path = urlparse(url).path.lower()
        if path.endswith('.pdf'):
            return 'PDF'
        elif path.endswith(('.html', '.htm')) or '.' not in path.split('/')[-1]:
            return 'HTML'
        return 'unknown'

async def main():
    file_path = "Tests/webScraping test/data/websites.csv"
    output_file = "Tests/webScraping test/data/scraped_data.csv"
    
    try:
        # Read URLs with proper error handling
        df = pd.read_csv(file_path)
        urls = df[['Name', 'URL', 'Type (HTML/XML, Javascript, PDF)']].to_dict('records')
        
        async with WebScraper() as scraper:
            tasks = []
            for url_info in urls:
                url = url_info['URL']
                title = url_info['Name']
                url_type = scraper.detect_website_type(url)
                
                if url_type == 'PDF':
                    task = scraper.scrape_pdf(url, title)
                else:
                    task = scraper.scrape_html(url, title)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with better error handling
            processed_data = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed: {str(result)}")
                    continue
                if isinstance(result, dict):
                    processed_data.append(result)
            
            # Save results with consistent column structure
            if processed_data:
                df_output = pd.DataFrame(processed_data)
                df_output = df_output.fillna('')  # Handle missing values
                df_output.to_csv(output_file, index=False)
                logger.info(f"Scraping completed. Saved {len(processed_data)} results to {output_file}")
            else:
                logger.error("No valid results to save")
                
    except Exception as e:
        logger.error(f"Main process error: {str(e)}")
        raise

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    logger.info(f"Total execution time: {time.time() - start_time:.2f} seconds")