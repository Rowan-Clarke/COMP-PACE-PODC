import pandas as pd

# Load URLs from an Excel or CSV file
def load_urls(file_path):
    # Read the file into a DataFrame
    df = pd.read_csv(file_path)  # Use read_csv() for CSV files
    urls = df['URL'].tolist()  # The column containing URLs is named 'URL'
    return urls

# Example usage
file_path = "websites.csv"  #CSV file containing URLS
url_list = load_urls(file_path)
print(f"Loaded {len(url_list)} URLs.")

websiteData = pd.read_csv("websites.csv")


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Initialize Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))


# Function to scrape data from a single URL
def scrape_data(url):
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
    
    return {"URL": url, "Title": title, "Content": content_text}


# Example usage
scraped_data = []
for url in url_list:
    try:
        data = scrape_data(url)
        scraped_data.append(data)
        print(f"Scraped data from {url}")
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")


# Save scraped data to a CSV file
def save_to_csv(data, output_file):
    df = pd.DataFrame(data)  # Convert list of dictionaries to DataFrame
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")


    # Example usage
output_file = "scraped_data_pdfTest.csv"
save_to_csv(scraped_data, output_file)
