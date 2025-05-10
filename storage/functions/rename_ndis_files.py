import os

def rename_ndis_files(directory):
    # Define the text to find and replace
    old_prefix = "National Disability Insurance Scheme"
    new_prefix = "NDIS"
    
    # Walk through the directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.startswith(old_prefix):
                # Create the new filename by replacing only at the start
                new_filename = new_prefix + filename[len(old_prefix):]
                
                # Create full file paths
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                
                try:
                    # Rename the file
                    os.rename(old_path, new_path)
                    print(f"Renamed: {filename} -> {new_filename}")
                except OSError as e:
                    print(f"Error renaming {filename}: {e}")

if __name__ == "__main__":
    directory = os.getcwd()
    
    print("Starting NDIS file rename process...")
    rename_ndis_files(directory)
    print("Rename process completed!")