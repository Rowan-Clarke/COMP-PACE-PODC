import os

def append_old_to_files(directory):
    """Appends '_OLD' to all filenames in the specified directory."""
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Split filename into name and extension
            name, ext = os.path.splitext(filename)
            
            # Create new filename with '_OLD' appended before extension
            new_filename = f"{name}_OLD{ext}"
            
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
    # Get the current directory where the script is running
    current_directory = os.getcwd()
    
    print("Starting file rename process...")
    append_old_to_files(current_directory)
    print("Rename process completed!")