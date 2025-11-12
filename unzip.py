import zipfile
import os

# Path to your zip file
zip_path = "gemini_client.zip"

# Choose where to extract it — here it’ll go into ./gemini_client/
extract_dir = os.path.join(os.getcwd(), "gemini_client")

# Create the folder if it doesn’t exist
os.makedirs(extract_dir, exist_ok=True)

# Unzip the file
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print(f"✅ Extracted all files to: {extract_dir}")
