import os
def rename_copy_files(directory):
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.startswith("Copy of "):
                # Create the new filename by removing "Copy of "
                new_filename = filename[8:]  # "Copy of " is 8 characters
                
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
    rename_copy_files(current_directory)
    print("Rename process completed!")