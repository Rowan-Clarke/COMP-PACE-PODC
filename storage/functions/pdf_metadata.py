from PyPDF2 import PdfReader, PdfWriter
import os
import pandas as pd

def add_pdf_metadata(pdf_path, url):
    """Add source URL to PDF metadata."""
    try:
        # Open the PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Copy pages
        for page in reader.pages:
            writer.add_page(page)

        # Add metadata
        writer.add_metadata({
            "/SourceURL": url
        })

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
    """Add URLs to PDFs based on Excel/CSV file data."""
    try:
        # Read the data file based on extension
        if data_path.lower().endswith('.csv'):
            df = pd.read_csv(data_path)
        else:
            df = pd.read_excel(data_path)
        
        # Ensure required columns exist
        if 'Name' not in df.columns or 'URL' not in df.columns:
            raise ValueError("Data file must contain 'Name' and 'URL' columns")
        
        successful = 0
        failed = 0
        
        # Process each row
        for index, row in df.iterrows():
            pdf_name = row['Name']
            url = row['URL']
            
            # Skip if URL is empty or NaN
            if pd.isna(url) or str(url).strip() == '':
                print(f"Skipping {pdf_name} - No URL provided")
                continue
            
            # Search for PDF in all subdirectories
            pdf_path = find_pdf_in_subdirectories(pdf_directory, pdf_name)
            
            if pdf_path is None:
                print(f"PDF not found in any subdirectory: {pdf_name}")
                failed += 1
                continue
            
            # Add metadata
            if add_pdf_metadata(pdf_path, str(url)):
                successful += 1
                print(f"Successfully added URL to {pdf_name}")
                print(f"Location: {pdf_path}")
            else:
                failed += 1
                print(f"Failed to add URL to {pdf_name}")
        
        print(f"\nBatch processing complete:")
        print(f"Successfully processed: {successful}")
        print(f"Failed: {failed}")
        
    except Exception as e:
        print(f"Error processing batch: {e}")

if __name__ == "__main__":
    # Use relative paths
    base_dir = "storage\data"
    data_file = os.path.join(base_dir, "data", "Grouped_Data", "URL_METADATA.csv")
    pdf_dir = os.path.join(base_dir, "data", "Grouped_Data", "COMBINED")
    
    print("Starting batch metadata addition...")
    print(f"Reading metadata from: {data_file}")
    print(f"Processing PDFs in: {pdf_dir}")
    batch_add_metadata(data_file, pdf_dir)
