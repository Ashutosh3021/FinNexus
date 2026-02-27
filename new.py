import os
import shutil

# Current directory
source_dir = os.getcwd()

# Target directory
target_dir = os.path.join(source_dir, "docs")

# Create docs folder if it doesn't exist
os.makedirs(target_dir, exist_ok=True)

# Loop through files
for filename in os.listdir(source_dir):
    if filename.endswith(".md") or filename.endswith(".txt"):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        # Move file
        shutil.move(source_path, target_path)
        print(f"Moved: {filename}")

print("Done.")