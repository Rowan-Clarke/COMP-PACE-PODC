import pdfkit
import pandas as pd
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import os
import logging
import requests  # Add this import
import re

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

    def get_categorized_filepath(self, title: str, category: str) -> str:
        """Create category directory and return full filepath"""
        # Clean the filename and category
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_category = re.sub(r'[<>:"/\\|?*]', '', category)
        
        # Create category directory
        category_dir = os.path.join(self.output_dir, safe_category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Create filename with category
        filename = f"{safe_title} _ {safe_category}.pdf"
        return os.path.join(category_dir, filename)

    def download_pdf(self, url: str, title: str, category: str) -> bool:
        """Download existing PDF files"""
        if not self.check_robots_txt(url):
            logging.error(f"Failed to download PDF {url}: Blocked by robots.txt")
            return False

        output_file = self.get_categorized_filepath(title, category)
        
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
            
            # Check if content appears to be PDF
            content_type = response.headers.get('content-type', '').lower()
            if not ('pdf' in content_type or response.content.startswith(b'%PDF')):
                logging.error(f"Failed to download PDF {url}: Content is not a PDF (received {content_type})")
                return False
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
                
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

    def convert_url_to_pdf(self, url: str, title: str, category: str) -> bool:
        if not self.check_robots_txt(url):
            logging.error(f"Failed to convert {url}: Blocked by robots.txt")
            return False
            
        output_file = self.get_categorized_filepath(title, category)
        
        options = {
            'quiet': '',
            'no-images': '',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'custom-header': [
                ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            ]
        }
        
        try:
            pdfkit.from_url(url, output_file, options=options, configuration=self.config)
            return True
        except Exception as e:
            if "ContentNotFoundError" in str(e):
                logging.error(f"Failed to convert {url}: Page not found")
            elif "Exit with code 1" in str(e):
                logging.error(f"Failed to convert {url}: Conversion error - possibly JavaScript-heavy page")
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