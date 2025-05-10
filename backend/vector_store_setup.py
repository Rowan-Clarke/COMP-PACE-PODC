from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from datetime import datetime
import time

# Setup project paths
project_root = Path(__file__).parent.parent.resolve()
tests_path = project_root / "storage/data"

# Add paths to Python path
sys.path.append(str(project_root))
sys.path.append(str(tests_path))

# Import the file_catalog function - use explicit import from Tests directory
from storage.functions.file_catalog import create_file_catalog

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_catalog_metadata(directory):
    """
    Generate catalog and return metadata dictionary
    """
    try:
        # Ensure directory is absolute path
        directory = Path(directory).resolve()
        
        # Create catalog using existing function
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'file_catalog_{timestamp}.xlsx'
        
        # Call create_file_catalog with absolute path
        create_file_catalog(str(directory))
        
        # Wait briefly to ensure file is written
        time.sleep(1)
        
        # Look for the generated file in the current working directory
        catalog_files = list(Path('.').glob(f'file_catalog_*.xlsx'))
        if not catalog_files:
            raise FileNotFoundError("No catalog file found")
            
        # Use the most recent catalog file
        latest_catalog = max(catalog_files, key=lambda p: p.stat().st_mtime)
        print(f"Reading catalog from: {latest_catalog.absolute()}")
        
        # Read the generated catalog
        df = pd.read_excel(latest_catalog)
        
        # Convert to dictionary with filename as key
        metadata_dict = {}
        for _, row in df.iterrows():
            metadata_dict[row['Name']] = {
                'filename': row['Name'],
                'category': row['Category'],
                'url': row['Source URL'] if row['Source URL'] != 'No URL found' else None,
                'version': row['Version'],
                'last_modified': row['Date Modified']
            }
        
        return metadata_dict
        
    except Exception as e:
        print(f"Error in get_catalog_metadata: {e}")
        return {}

def process_files(directory, vector_store_id):
    """
    Process files and upload them to OpenAI with metadata
    """
    files_with_metadata = []
    
    # Get metadata from catalog
    catalog_metadata = get_catalog_metadata(directory)
    
    for file_path in Path(directory).glob('**/*.pdf'):
        try:
            filename = file_path.name
            # Use catalog metadata if available, fallback to PDF extraction
            if filename in catalog_metadata:
                metadata = catalog_metadata[filename]
            else:
                metadata = get_file_metadata(file_path)
            
            # Upload file first
            with open(file_path, 'rb') as file:
                uploaded_file = client.files.create(
                    file=file,
                    purpose="assistants"
                )
                
                # Create vector store file with metadata as attributes
                vector_file = client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=uploaded_file.id,
                    attributes={
                        'filename': metadata['filename'],
                        'category': metadata['category'],
                        'url': metadata['url'] if metadata['url'] else '',
                        'version': str(metadata['version']),
                        'last_modified': str(metadata['last_modified'])
                    }
                )
                
                files_with_metadata.append((vector_file.id, metadata))
                print(f"Uploaded and processed {filename}: {vector_file.id}")
                print(f"Metadata attributes: {vector_file.attributes}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return files_with_metadata

def create_vector_store():
    """Create a new vector store"""
    try:
        response = client.vector_stores.create(
            name="podc_knowledge_base_attributes",
        )
        print(f"Created vector store with ID: {response.id}")
        return response.id
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def create_file_batch(vector_store_id, files_with_metadata):
    """
    Create a vector store file batch
    """
    try:
        # Extract file IDs and metadata
        file_ids = [f[0] for f in files_with_metadata]
        
        # Create the file batch
        batch = client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=file_ids
        )
        return batch
    except Exception as e:
        print(f"Error creating file batch: {e}")
        return None

def main():
    # Use absolute path for base directory
    base_dir = Path(project_root) / "storage\data\Grouped_Data\COMBINED"
    base_dir = base_dir.resolve()
    
    print(f"Processing files in: {base_dir}")
    
    # First create a vector store
    vector_store_id = create_vector_store()
    if not vector_store_id:
        print("Failed to create vector store")
        return
    
    # Process and upload files
    files_with_metadata = process_files(base_dir, vector_store_id)
    
    if not files_with_metadata:
        print("No files were processed successfully")
        return
    
    # Create file batch in the vector store
    batch = create_file_batch(vector_store_id, files_with_metadata)
    
    if batch:
        print(f"Successfully created file batch: {batch.id}")
        print(f"Status: {batch.status}")
        
        # Monitor the batch status
        try:
            while batch.status == "in_progress":
                # Wait a bit before checking again
                time.sleep(5)
                # Get updated status
                batch = client.vector_stores.file_batches.retrieve(
                    vector_store_id=vector_store_id,
                    batch_id=batch.id
                )
                print(f"Batch status: {batch.status}")
                print(f"File counts: {batch.file_counts}")
                
            if batch.status == "completed":
                print("Successfully processed all files")
            else:
                print(f"Batch processing ended with status: {batch.status}")
                
        except Exception as e:
            print(f"Error monitoring batch status: {e}")
    else:
        print("Failed to create file batch")

if __name__ == "__main__":
    main()