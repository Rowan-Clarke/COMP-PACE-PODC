import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
import os
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

# Load URLs from a CSV file
def load_urls(file_path):
    df = pd.read_csv(file_path)  # Read the CSV file
    urls = df[['Name', 'URL', 'Type (HTML/XML, Javascript, PDF)']].to_dict('records')  # Extract Name, URL, and type
    return urls

# Initialize Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Function to scrape data from an HTML URL
def scrape_html(url):
    driver.get(url)  # Open the webpage
    html = driver.page_source  # Get HTML content
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract relevant data (customize selectors based on target website)
    title = soup.title.text if soup.title else "No title found"
    main_content = soup.find("div", class_="content-type-content")  # Example selector
    
    if main_content:
        content_text = main_content.get_text().strip()
    else:
        content_text = "No content found"
    
    return {"Title": title, "Content": content_text}

# Function to scrape data from a PDF URL
def scrape_pdf(url, title):
    response = requests.get(url)
    if response.status_code == 200:
        pdf_file_path = "temp.pdf"
        with open(pdf_file_path, "wb") as pdf_file:
            pdf_file.write(response.content)  # Save the PDF locally
        
        # Extract text from the PDF
        reader = PdfReader(pdf_file_path)
        content_text = ""
        for page in reader.pages:
            content_text += page.extract_text() + "\n"
        
        # Clean up the temporary PDF file
        os.remove(pdf_file_path)
        
        return {"Title": title, "Content": content_text.strip()}
    else:
        return {"Title": title, "Content": "Failed to download PDF"}

# Function to check robots.txt
def check_robots_permission(url):
    try:
        # Parse the URL to get the base domain
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        # Initialize and read robots.txt
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        # Check if scraping is allowed for this path
        can_fetch = rp.can_fetch("*", url)
        return can_fetch
    except Exception as e:
        print(f"Error checking robots.txt for {url}: {e}")
        return False

def detect_website_type(url):
    """Determine the type of website based on URL and content"""
    if url.lower().endswith('.pdf'):
        return 'PDF'
    elif url.lower().endswith(('.html', '.htm')) or not url.lower().split('?')[0].split('/')[-1].endswith(('.', '/')):
        return 'HTML'
    else:
        return 'unknown'

def check_accessibility(url, content):
    """Check if the website is accessible based on content"""
    error_phrases = ['404', 'not found', 'no content here', 'missing', 'error', 'page not found']
    
    try:
        response = requests.head(url, timeout=10)
        if response.status_code != 200:
            return 'NO'
            
        if isinstance(content, str):
            content_lower = content.lower()
            if any(phrase in content_lower for phrase in error_phrases):
                return 'NO'
        return 'YES'
    except:
        return 'NO'

def analyze_and_update_csv(input_file):
    """Analyze URLs and update CSV with additional information"""
    df = pd.read_csv(input_file)
    
    # Add new columns if they don't exist
    if 'Type (HTML/XML, Javascript, PDF)' not in df.columns:
        df['Type (HTML/XML, Javascript, PDF)'] = df['URL'].apply(detect_website_type)
    
    if 'Robots.txt permission?' not in df.columns:
        df['Robots.txt permission?'] = df['URL'].apply(lambda x: 'YES' if check_robots_permission(x) else 'NO')
    
    if 'Accessible?' not in df.columns:
        df['Accessible?'] = 'Unknown'  # Will be updated during scraping
    
    # Save updated CSV
    df.to_csv(input_file, index=False)
    return df.to_dict('records')

# Main function to scrape data from URLs
def scrape_data(urls):
    scraped_data = []
    updated_records = []
    
    for url_info in urls:
        url = url_info['URL']
        url_type = url_info.get('Type (HTML/XML, Javascript, PDF)', detect_website_type(url))
        title = url_info['Name']
        
        # Create record for updating the input CSV
        record = {
            'Name': title,
            'URL': url,
            'Type (HTML/XML, Javascript, PDF)': url_type,
            'Robots.txt permission?': 'YES' if check_robots_permission(url) else 'NO'
        }
        
        try:
            if not check_robots_permission(url):
                print(f"Scraping disallowed for {url}")
                content = "Scraping disallowed by robots.txt"
                record['Accessible?'] = 'NO'
            else:
                if url_type == "HTML":
                    data = scrape_html(url)
                    content = data.get('Content', '')
                elif url_type == "PDF":
                    data = scrape_pdf(url, title)
                    content = data.get('Content', '')
                else:
                    content = "Unsupported file type"
                
                record['Accessible?'] = check_accessibility(url, content)
            
            scraped_data.append({
                "URL": url,
                "Title": title,
                "Content": content
            })
            
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            content = str(e)
            record['Accessible?'] = 'NO'
            scraped_data.append({
                "URL": url,
                "Title": title,
                "Content": content
            })
        
        updated_records.append(record)
    
    # Update the input CSV with accessibility information
    df = pd.DataFrame(updated_records)
    df.to_csv('Tests/webScraping test/data/websites.csv', index=False)
    
    return scraped_data

# Save scraped data to a CSV file
def save_to_csv(data, output_file):
    df = pd.DataFrame(data)  # Convert list of dictionaries to DataFrame
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

# Example usage
if __name__ == "__main__":
    file_path = "Tests/webScraping test/data/websites.csv"
    output_file = "Tests/webScraping test/data/scraped_data.csv"
    
    # First analyze and update the input CSV
    url_list = analyze_and_update_csv(file_path)
    print(f"Loaded and analyzed {len(url_list)} URLs.")
    
    # Then perform the scraping
    scraped_data = scrape_data(url_list)
    save_to_csv(scraped_data, output_file)
    print("Scraping completed. Input and output files have been updated.")