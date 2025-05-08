import os
import pandas as pd
from datetime import datetime

def create_file_catalog(root_directory):
    # Lists to store file information
    file_names = []
    mod_dates = []  # New list for modification dates
    categories = []
    versions = []
    sizes = []

    # Walk through the directory
    for root, dirs, files in os.walk(root_directory):
        # Get the immediate parent folder name (category)
        category = os.path.basename(root)
        
        # Skip the root directory itself
        if root == root_directory:
            continue
            
        # Process each file
        for file in files:
            file_path = os.path.join(root, file)
            file_names.append(file)
            
            # Get file modification time
            mod_timestamp = os.path.getmtime(file_path)
            mod_datetime = datetime.fromtimestamp(mod_timestamp)
            mod_dates.append(mod_datetime.strftime('%Y-%m-%d %H:%M:%S'))
            
            categories.append(category)
            
            # Get file size in kilobytes
            size_kb = round(os.path.getsize(file_path) / 1024, 2)
            sizes.append(size_kb)
            
            # Determine version based on file name
            if file.endswith('_OLD.pdf'):
                versions.append('OLD')
            elif file.endswith('_NEW.pdf'):
                versions.append('NEW')
            else:
                versions.append('UNKNOWN')
    
    # Create a DataFrame with five columns
    df = pd.DataFrame({
        'Name': file_names,
        'Date Modified': mod_dates,
        'Category': categories,
        'Version': versions,
        'Size (KB)': sizes
    })
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'file_catalog_{timestamp}.xlsx'
    
    # Save to Excel
    try:
        df.to_excel(output_file, index=False)
        print(f"Catalog created successfully: {output_file}")
        print(f"Total files processed: {len(file_names)}")
    except Exception as e:
        print(f"Error creating Excel file: {e}")

if __name__ == "__main__":
    directory = r"C:\Users\dylan\COMP3850\COMP-PACE-PODC\Tests\webScraping_test\data\Grouped_Data\COMBINED"
    
    print("Starting catalog creation...")
    create_file_catalog(directory)