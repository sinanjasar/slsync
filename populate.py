import os
import yaml
import shutil

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Get folders from config
download_folder = config["DOWNLOAD_FOLDERS"][0]
dest_folder = config["DEST_FOLDER"]
test_files = "/Users/sinanjasar/slsync/test_files"

# Copy all files from test_files to download_folder
for filename in os.listdir(test_files):
    src_path = os.path.join(test_files, filename)
    dst_path = os.path.join(download_folder, filename)
    shutil.copy(src_path, dst_path)