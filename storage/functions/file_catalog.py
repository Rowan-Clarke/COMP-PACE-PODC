import os
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfReader

def create_file_catalog(root_directory, output_directory=None):
    # Lists to store file information
    file_names = []
    mod_dates = []
    categories = []
    sizes = []
    source_urls = []
    titles = []      
    authors = []     

    # Walk through the directory
    for root, dirs, files in os.walk(root_directory):
        category = os.path.basename(root)
        
        if root == root_directory:
            continue
            
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue

            file_path = os.path.join(root, file)
            file_names.append(file)
            
            # Get file modification time
            mod_timestamp = os.path.getmtime(file_path)
            mod_datetime = datetime.fromtimestamp(mod_timestamp)
            mod_dates.append(mod_datetime.strftime('%Y-%m-%d %H:%M:%S'))
            
            categories.append(category)
            
            # Get file size
            size_kb = round(os.path.getsize(file_path) / 1024, 2)
            sizes.append(size_kb)

            # Get metadata from PDF
            try:
                reader = PdfReader(file_path)
                url = reader.metadata.get('/SourceURL', 'No URL found')
                title = reader.metadata.get('/Title', 'No title found')
                author = reader.metadata.get('/Author', 'No author found')
                
                source_urls.append(url)
                titles.append(title)
                authors.append(author)
            except Exception as e:
                source_urls.append('Error reading metadata')
                titles.append('Error reading metadata')
                authors.append('Error reading metadata')
    
    # Create DataFrame with eight columns
    df = pd.DataFrame({
        'Name': file_names,
        'Title': titles,
        'Author': authors,
        'Date Modified': mod_dates,
        'Category': categories,
        'Size (KB)': sizes,
        'Source URL': source_urls
    })
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'file_catalog_{timestamp}.xlsx'
    
    # If output directory is specified, join it with filename
    if output_directory:
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_file = os.path.join(output_directory, output_file)
    
    try:
        df.to_excel(output_file, index=False)
        print(f"Catalog created successfully: {output_file}")
        print(f"Total files processed: {len(file_names)}")
    except Exception as e:
        print(f"Error creating Excel file: {e}")

if __name__ == "__main__":
    directory = r"storage\data\PDFs"
    output_dir = r"storage\data\Catalogs"

    # Add directory existence check
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {os.path.abspath(directory)}")
        exit(1)

    print("Starting catalog creation...")
    print(f"Scanning directory: {os.path.abspath(directory)}")
    create_file_catalog(directory, output_dir)