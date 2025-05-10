import csv
import os
import re

# filepath: c:\Users\dylan\COMP3850\COMP-PACE-PODC\webScraping test\generate_txt_files.py
# Define the input CSV file path
csv_file_path = "storage\data\scraped_data.csv"

# Define the output directory for the text files
output_dir = "storage\data\output_txt_files"

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

def sanitize_filename(title):
    """Clean the title to make it a valid filename"""
    # Replace problematic characters
    clean_title = title.strip()
    # Replace colons, question marks and other special characters
    clean_title = re.sub(r'[:|?/\\<>*"]', '', clean_title)
    # Replace spaces and multiple underscores with single underscore
    clean_title = re.sub(r'\s+', '_', clean_title)
    clean_title = re.sub(r'_+', '_', clean_title)
    return clean_title

# Read the CSV file and generate text files
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    file_count = 0
    
    for row in csv_reader:
        try:
            # Get the title and content from the row
            title = sanitize_filename(row['Title'])
            content = row['Content']

            # Define the output text file path
            txt_file_path = os.path.join(output_dir, f"{title}.txt")

            # Write the content to the text file
            with open(txt_file_path, mode='w', encoding='utf-8') as txt_file:
                txt_file.write(content)
            
            file_count += 1
            print(f"Created file: {txt_file_path}")
            
        except Exception as e:
            print(f"Error processing row: {e}")

print(f"\nTotal files created: {file_count}")
print(f"Files have been generated in the directory: {output_dir}")