import os
import pandas as pd
from PyPDF2 import PdfReader
import unicodedata
from datetime import datetime
import sys

# Set console to UTF-8 mode
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    os.system('chcp 65001')

def normalize_text(text):
    if not text:
        return ''
    # Handle UTF-8 encoding explicitly
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    normalized = unicodedata.normalize('NFKD', str(text))
    # Replace problematic characters
    normalized = normalized.replace('â€™', "'")
    normalized = normalized.replace('â€"', "-")
    return normalized.strip()

def generate_metadata_csv(root_directory, output_directory=None):
    print("Starting File Summary creation...")
    print(f"Scanning directory: {os.path.abspath(root_directory)}")
    
    # Lists to store file information
    names = []
    urls = []
    titles = []
    authors = []

    # Walk through the directory
    for root, dirs, files in os.walk(root_directory):
        if root == root_directory:
            continue
            
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'rb') as pdf_file:
                    reader = PdfReader(pdf_file)
                    metadata = reader.metadata
                    
                    names.append(normalize_text(file))
                    urls.append(normalize_text(metadata.get('/SourceURL', '')))
                    titles.append(normalize_text(metadata.get('/Title', '')))
                    authors.append(normalize_text(metadata.get('/Author', '')))
                
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
                names.append(normalize_text(file))
                urls.append('Error reading metadata')
                titles.append('Error reading metadata')
                authors.append('Error reading metadata')
    
    if names:
        df = pd.DataFrame({
            'Name': names,
            'URL': urls,
            'Title': titles,
            'Author': authors
        })
        
        # Generate output filename
        output_file = 'metadata_test.csv'
        
        # If output directory is specified, join it with filename
        if output_directory:
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            output_file = os.path.join(output_directory, output_file)
        
        try:
            # Write CSV with UTF-8 encoding and BOM
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Metadata has been written to: {output_file}")
            print(f"Total files processed: {len(names)}")
        except Exception as e:
            print(f"Error creating CSV file: {e}")
    else:
        print("No PDF files found in the directory.")

if __name__ == "__main__":
    directory = r"storage\data\PDFs\files"
    output_dir = r"storage\data"

    # Add directory existence check
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {os.path.abspath(directory)}")
        exit(1)

    generate_metadata_csv(directory, output_dir)
