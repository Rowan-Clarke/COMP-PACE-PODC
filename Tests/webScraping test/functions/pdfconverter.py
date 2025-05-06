import pdfkit
import pandas as pd
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import os
import logging
import requests  # Add this import
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WebsiteToPdfConverter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
        # Initialize Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--window-size=1920,1080')

    def get_domain_owner(self, url: str) -> str:
        """Extract and clean domain name from URL"""
        domain = urlparse(url).netloc.lower()
        # Remove www. and .com/.org/.gov etc
        domain = re.sub(r'^www\.', '', domain)
        domain = re.sub(r'\.(?:com|org|gov|edu|net)\.[a-z]{2}$|\.(?:com|org|gov|edu|net)$', '', domain)
        # Convert to title case and replace dots with spaces
        return domain.replace('.', ' ').title()

    def get_categorized_filepath(self, title: str, category: str, url: str) -> str:
        """Create category directory and return full filepath with owner"""
        try:
            # Clean and heavily truncate filename components
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
            safe_category = re.sub(r'[<>:"/\\|?*]', '', category)
            owner = self.get_domain_owner(url)
            
            # Much shorter components
            title_part = safe_title[:30] if len(safe_title) > 30 else safe_title
            owner_part = owner[:20] if len(owner) > 20 else owner
            category_part = safe_category[:20] if len(safe_category) > 20 else safe_category
            
            # Create shorter category directory
            category_dir = os.path.join(self.output_dir, category_part)
            os.makedirs(category_dir, exist_ok=True)
            
            # Create shorter filename
            filename = f"{title_part}_{owner_part}.pdf"
            output_file = os.path.join(category_dir, filename)
            
            # Final length check
            if len(output_file) > 240:
                filename = f"{title_part[:20]}_{owner_part[:10]}.pdf"
                output_file = os.path.join(category_dir, filename)
                
            return output_file
            
        except Exception as e:
            logging.error(f"File system error: {str(e)}")
            raise

    def is_valid_pdf(self, content: bytes, content_type: str) -> bool:
        """Verify if content is actually a valid PDF"""
        # Check magic number for PDF
        pdf_signature = b'%PDF-'
        if not content.startswith(pdf_signature):
            return False
        
        # Check content type
        if not ('pdf' in content_type.lower() and 'html' not in content_type.lower()):
            return False
            
        # Check minimum valid size (500 bytes)
        if len(content) < 500:
            return False
            
        return True

    def download_pdf(self, url: str, title: str, category: str) -> bool:
        """Download existing PDF files"""
        if not self.check_robots_txt(url):
            logging.error(f"Failed to download PDF {url}: Blocked by robots.txt")
            return False

        output_file = self.get_categorized_filepath(title, category, url)
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*'
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=True)
            
            # Handle specific HTTP errors
            if response.status_code == 403:
                logging.error(f"Failed to download PDF {url}: Access forbidden (403)")
                return False
            elif response.status_code == 404:
                logging.error(f"Failed to download PDF {url}: File not found (404)")
                return False
            
            response.raise_for_status()
            
            # Enhanced PDF validation
            content_type = response.headers.get('content-type', '').lower()
            if not self.is_valid_pdf(response.content, content_type):
                logging.error(f"Failed to download PDF {url}: Invalid PDF format or corrupted content")
                return False
            
            with open(output_file, 'wb') as f:
                # Write in chunks to handle large files
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                f.flush()
                os.fsync(f.fileno())  # Ensure content is written to disk
                
            logging.info(f"Successfully saved PDF to {output_file}")
            return True
            
        except requests.exceptions.SSLError:
            logging.error(f"Failed to download PDF {url}: SSL/TLS verification failed")
            return False
        except requests.exceptions.ConnectionError:
            logging.error(f"Failed to download PDF {url}: Connection failed or timed out")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download PDF {url}: Network error - {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Failed to download PDF {url}: Unexpected error - {str(e)}")
            return False
        
    def check_robots_txt(self, url: str) -> bool:
        domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        parser = RobotFileParser()
        parser.set_url(f"{domain}/robots.txt")
        try:
            parser.read()
            return parser.can_fetch("*", url)
        except Exception as e:
            logging.warning(f"Could not check robots.txt for {domain}: {e}")
            return True

    def convert_with_selenium(self, url: str, output_file: str) -> bool:
        """Use Selenium for JavaScript-heavy pages"""
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.chrome_options
            )
            
            driver.get(url)
            # Wait for JavaScript content to load
            time.sleep(5)
            
            # Set up PDF printing preferences
            print_options = {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True,
            }
            
            # Print to PDF
            pdf = driver.print_page(print_options)
            
            # Save the PDF
            with open(output_file, 'wb') as f:
                f.write(pdf)
            
            driver.quit()
            return True
            
        except Exception as e:
            logging.error(f"Selenium conversion failed: {str(e)}")
            return False

    def convert_url_to_pdf(self, url: str, title: str, category: str) -> bool:
        if not self.check_robots_txt(url):
            logging.error(f"Failed to convert {url}: Blocked by robots.txt")
            return False
            
        output_file = self.get_categorized_filepath(title, category, url)
        
        # Try with pdfkit first
        try:
            options = {
                'quiet': '',
                'no-images': '',
                'encoding': 'UTF-8',
                'enable-local-file-access': None,
                'custom-header': [
                    ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                ],
                'javascript-delay': 2000,  # Increased delay
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }
            
            pdfkit.from_url(url, output_file, options=options, configuration=self.config)
            return True
            
        except Exception as e:
            if "javascript" in str(e).lower() or "Exit with code 1" in str(e):
                logging.info(f"Attempting Selenium fallback for {url}")
                if self.convert_with_selenium(url, output_file):
                    logging.info(f"Successfully converted with Selenium: {url}")
                    return True
                    
            if "ContentNotFoundError" in str(e):
                logging.error(f"Failed to convert {url}: Page not found")
            else:
                logging.error(f"Failed to convert {url}: {e}")
            return False

def main():
    # Create the downloads directory with proper path
    download_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Downloads")
    converter = WebsiteToPdfConverter(download_dir)
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "websites.csv")
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        url = row['URL'].strip()
        title = row['Name'].strip()
        category = row['Category'].strip()
        
        if url.lower().endswith('.pdf'):
            logging.info(f"Attempting to download PDF: {title}")
            success = converter.download_pdf(url, title, category)
            if success:
                logging.info(f"Successfully downloaded PDF: {title}")
            else:
                logging.error(f"Failed to download PDF: {title}")
        else:
            success = converter.convert_url_to_pdf(url, title, category)
            if success:
                logging.info(f"Successfully converted {title}")
            else:
                logging.error(f"Failed to convert {title}")

if __name__ == "__main__":
    main()