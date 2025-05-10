import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def check_vector_store(vector_store_id="vs_681c6bc049b88191897ea7a338837d7c"):
    try:
        print(f"\nChecking Vector Store: {vector_store_id}")
        print("=" * 50)
        
        # Get vector store files
        vector_store_files = client.vector_stores.files.list(vector_store_id)
        
        # Create a list to store file data
        files_data = []
        
        # Extract relevant information from each file
        for file in vector_store_files.data:
            file_data = {
                'File ID': file.id,
                'Attributes': json.dumps(file.attributes, indent=2) if file.attributes else "No attributes",
                'Created At': datetime.fromtimestamp(file.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'Status': file.status,
                'Usage Bytes': file.usage_bytes,
                'Last Error': file.last_error.message if file.last_error else None,
                'Max Chunk Size': file.chunking_strategy.static.max_chunk_size_tokens,
                'Chunk Overlap': file.chunking_strategy.static.chunk_overlap_tokens
            }
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