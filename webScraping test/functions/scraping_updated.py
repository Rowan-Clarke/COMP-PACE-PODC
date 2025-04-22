import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from PyPDF2 import PdfReader
import os

# Load URLs from a CSV file
def load_urls(file_path):
    df = pd.read_csv(file_path)  # Read the CSV file
    urls = df[['URL', 'Type (HTML/XML, Javascript, PDF)']].to_dict('records')  # Extract URL and type
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
def scrape_pdf(url):
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
        
        return {"Title": "PDF Content", "Content": content_text.strip()}
    else:
        return {"Title": "No title found", "Content": "Failed to download PDF"}

# Main function to scrape data from URLs
def scrape_data(urls):
    scraped_data = []
    for url_info in urls:
        url = url_info['URL']
        url_type = url_info['Type (HTML/XML, Javascript, PDF)']
        try:
            if url_type == "HTML":
                data = scrape_html(url)
            elif url_type == "PDF":
                data = scrape_pdf(url)
            else:
                data = {"Title": "Unsupported Type", "Content": "No content extracted"}
            
            data["URL"] = url  # Add the URL to the data
            scraped_data.append(data)
            print(f"Scraped data from {url}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            scraped_data.append({"URL": url, "Title": "Error", "Content": str(e)})
    return scraped_data

# Save scraped data to a CSV file
def save_to_csv(data, output_file):
    df = pd.DataFrame(data)  # Convert list of dictionaries to DataFrame
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

# Example usage
if __name__ == "__main__":
    file_path = "webScraping test\data\websites.csv"  # Input CSV file containing URLs
    output_file = "webScraping test\data\scraped_data_pdftest.csv"  # Output CSV file
    
    url_list = load_urls(file_path)
    print(f"Loaded {len(url_list)} URLs.")
    
    scraped_data = scrape_data(url_list)
    save_to_csv(scraped_data, output_file)