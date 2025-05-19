import os
import shutil
from pathlib import Path

def create_file_copies(source_dir, dest_dir):
    """
    Create copies of all PDF files from source directory and its subdirectories
    into a single destination directory.
    """
    try:
        # Ensure destination directory exists
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        # Counter for copied files
        count = 0
        
        # Walk through source directory
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    # Get full source path
                    source_path = os.path.join(root, file)
                    
                    # Create destination filename 
                    dest_name = f"{file}"
                    dest_path = os.path.join(dest_dir, dest_name)
                    
                    # Copy file
                    shutil.copy2(source_path, dest_path)
                    
                    count += 1
                    print(f"Copied file: {dest_name}")
        
        print(f"\nProcess complete: Copied {count} files")
        
    except Exception as e:
        print(f"Error copying files: {e}")

if __name__ == "__main__":
    # Define paths
    base_dir = Path(__file__).parent.parent.parent.resolve()
    source_dir = base_dir / "storage/data/PDFs/files"
    dest_dir = source_dir / ".ENTIRE CATALOG"  
    
    print("Copying all PDF files...")
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    create_file_copies(str(source_dir), str(dest_dir))