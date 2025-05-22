from PyPDF2 import PdfReader, PdfWriter
import os
import pandas as pd

def append_pdf_metadata(pdf_path, url, title=None, author=None):
    """Add source URL, title, and author to PDF metadata."""
    try:
        # Open the PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Copy pages
        for page in reader.pages:
            writer.add_page(page)

        # Prepare metadata
        metadata = {"/SourceURL": url}
        if title:
            metadata["/Title"] = title
        if author:
            metadata["/Author"] = author

        # Add metadata
        writer.add_metadata(metadata)

        # Save with new metadata
        temp_path = pdf_path + ".temp"
        with open(temp_path, "wb") as output_file:
            writer.write(output_file)

        # Replace original file
        os.replace(temp_path, pdf_path)
        return True
    except Exception as e:
        print(f"Error adding metadata to {pdf_path}: {e}")
        return False

def find_pdf_in_subdirectories(base_dir, filename):
    """Search for a PDF file in all subdirectories."""
    for root, _, files in os.walk(base_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def batch_add_metadata(data_path, pdf_directory):
    """Add metadata to PDFs based on Excel/CSV file data."""
    try:
        # Read the data file based on extension with different encodings
        if data_path.lower().endswith('.csv'):
            try:
                df = pd.read_csv(data_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(data_path, encoding='latin-1')
                except UnicodeDecodeError:
                    df = pd.read_csv(data_path, encoding='cp1252')
        else:
            df = pd.read_excel(data_path)
        
        # Ensure required columns exist
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Data file must contain 'Name' column")
        
        successful = 0
        failed = 0
        
        # Process each row
        for index, row in df.iterrows():
            pdf_name = row['Name']
            
            # Get metadata fields, use None if not present
            url = row.get('URL', None)
            title = row.get('Title', None)
            author = row.get('Author', None)
            
            # Search for PDF in all subdirectories
            pdf_path = find_pdf_in_subdirectories(pdf_directory, pdf_name)
            
            if pdf_path is None:
                print(f"PDF not found in any subdirectory: {pdf_name}")
                failed += 1
                continue
            
            # Skip if no metadata to add
            if all(x is None or pd.isna(x) or str(x).strip() == '' for x in [url, title, author]):
                print(f"Skipping {pdf_name} - No metadata provided")
                continue
            
            # Convert empty strings and NaN to None
            url = None if pd.isna(url) or str(url).strip() == '' else str(url)
            title = None if pd.isna(title) or str(title).strip() == '' else str(title)
            author = None if pd.isna(author) or str(author).strip() == '' else str(author)
            
            # Add metadata
            if append_pdf_metadata(pdf_path, url, title, author):
                successful += 1
                print(f"Successfully added metadata to {pdf_name}")
                print(f"Location: {pdf_path}")
                if title: print(f"Title: {title}")
                if author: print(f"Author: {author}")
                if url: print(f"URL: {url}")
            else:
                failed += 1
                print(f"Failed to add metadata to {pdf_name}")
        
        print(f"\nBatch processing complete:")
        print(f"Successfully processed: {successful}")
        print(f"Failed: {failed}")
        
    except Exception as e:
        print(f"Error processing batch: {e}")

if __name__ == "__main__":
    # Use relative paths
    base_dir = "storage\data"
    data_file = os.path.join(base_dir, "PDFS", "METADATA_TEST.csv")
    pdf_dir = os.path.join(base_dir, "PDFs", "files")
    
    print("Starting batch metadata addition...")
    print(f"Reading metadata from: {data_file}")
    print(f"Processing PDFs in: {pdf_dir}")
    batch_add_metadata(data_file, pdf_dir)
