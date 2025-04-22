import csv
import os

# filepath: c:\Users\dylan\COMP3850\COMP-PACE-PODC\webScraping test\generate_txt_files.py
# Define the input CSV file path
csv_file_path = "webScraping test\scraped_data.csv"

# Define the output directory for the text files
output_dir = "webScraping test\output_txt_files"

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Read the CSV file and generate text files
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        # Get the title and content from the row
        title = row['Title'].strip().replace(" ", "_").replace("|", "").replace("/", "_").replace("?", "QuestionMark")
        content = row['Content']

        # Define the output text file path
        txt_file_path = os.path.join(output_dir, f"{title}.txt")

        # Write the content to the text file
        with open(txt_file_path, mode='w', encoding='utf-8') as txt_file:
            txt_file.write(content)

print(f"Text files have been generated in the directory: {output_dir}")