import os
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfReader

def create_file_catalog(root_directory):
    # Lists to store file information
    file_names = []
    mod_dates = []
    categories = []
    versions = []
    sizes = []
    source_urls = []  # New list for URLs

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
            
            # Get version
            if file.endswith('_OLD.pdf'):
                versions.append('OLD')
            elif file.endswith('_NEW.pdf'):
                versions.append('NEW')
            else:
                versions.append('UNKNOWN')

            # Get source URL from metadata
            try:
                reader = PdfReader(file_path)
                url = reader.metadata.get('/SourceURL', 'No URL found')
                source_urls.append(url)
            except Exception as e:
                source_urls.append('Error reading metadata')
    
    # Create DataFrame with six columns
    df = pd.DataFrame({
        'Name': file_names,
        'Date Modified': mod_dates,
        'Category': categories,
        'Version': versions,
        'Size (KB)': sizes,
        'Source URL': source_urls
    })
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'file_catalog_{timestamp}.xlsx'
    
    try:
        df.to_excel(output_file, index=False)
        print(f"Catalog created successfully: {output_file}")
        print(f"Total files processed: {len(file_names)}")
    except Exception as e:
        print(f"Error creating Excel file: {e}")

if __name__ == "__main__":
    # Get the current directory where the script is running
    directory = "storage\data\Grouped_Data\COMBINED"

    print("Starting catalog creation...")
    create_file_catalog(directory)