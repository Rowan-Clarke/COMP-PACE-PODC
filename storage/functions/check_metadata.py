import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def check_vector_store(vector_store_id="vs_681eac93bf088191bd4f7de05e04dbbf"):
    try:
        print(f"\nChecking Vector Store: {vector_store_id}")
        print("=" * 50)
        
        # Create a list to store all files
        all_files = []
        
        # Initialize pagination
        after = None
        while True:
            # Get vector store files with pagination
            vector_store_files = client.vector_stores.files.list(
                vector_store_id,
                after=after
            )
            
            # Add files to our collection
            all_files.extend(vector_store_files.data)
            
            # Check if there are more files to fetch
            if not vector_store_files.has_more:
                break
                
            # Update the pagination cursor
            after = vector_store_files.last_id
        
        print(f"Total files found: {len(all_files)}")
        
        # Create a list to store file data
        files_data = []
        
        # Extract relevant information from each file
        for file in all_files:
            # Start with base file data
            file_data = {
                'File ID': file.id,
                'Created At': datetime.fromtimestamp(file.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'Status': file.status,
                'Usage Bytes': file.usage_bytes,
                'Last Error': file.last_error.message if file.last_error else None,
                'Max Chunk Size': file.chunking_strategy.static.max_chunk_size_tokens,
                'Chunk Overlap': file.chunking_strategy.static.chunk_overlap_tokens
            }
            
            # Add attributes as separate columns
            if file.attributes:
                # Store the original attributes JSON for reference
                file_data['Raw Attributes'] = json.dumps(file.attributes, indent=2)
                # Add attribute count
                file_data['Attribute Count'] = len(file.attributes)
                # Add each attribute as a separate column
                for key, value in file.attributes.items():
                    file_data[f'Attribute_{key}'] = value
            else:
                file_data['Raw Attributes'] = "No attributes"
                file_data['Attribute Count'] = 0
                
            files_data.append(file_data)
        
        # Create DataFrame
        df = pd.DataFrame(files_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f'vector_store_files_{timestamp}.xlsx'
        
        # Save to Excel
        df.to_excel(excel_filename, index=False)
        print(f"\nFile data exported to: {excel_filename}")
        
        return df
        
    except Exception as e:
        print(f"Error checking vector store: {e}")
        print(f"Error type: {type(e)}")
        return None

if __name__ == "__main__":
    check_vector_store()