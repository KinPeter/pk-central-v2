import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from ftplib import FTP

# Load environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

DUMP_DIR = "./dump"
FTP_UPLOAD_DIR = "/central-backup"

if not MONGODB_URI or not FTP_HOST or not FTP_USER or not FTP_PASS:
    raise Exception("Missing required environment variables.")

# Step 1: Dump MongoDB
if os.path.exists(DUMP_DIR):
    shutil.rmtree(DUMP_DIR)
subprocess.run(["mongodump", "--uri", MONGODB_URI, "--out", DUMP_DIR], check=True)
print(f"MongoDB dump completed to {DUMP_DIR}")

# Ensure the dump directory exists
if not os.path.exists(DUMP_DIR):
    raise Exception(f"Dump directory {DUMP_DIR} does not exist after mongodump.")

# Step 2: Zip the dump folder
now = datetime.now().strftime("%Y-%m-%d")
zip_filename = f"backup_{now}.zip"
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(DUMP_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            arcname = os.path.relpath(filepath, DUMP_DIR)
            zipf.write(filepath, arcname)

print(f"Backup created: {zip_filename}")

# Step 3: Upload to FTP
ftp = FTP(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)
ftp.cwd(FTP_UPLOAD_DIR)
with open(zip_filename, "rb") as f:
    ftp.storbinary(f"STOR {zip_filename}", f)

print(f"Backup uploaded to FTP: {zip_filename}")

# Clean up local zip file
os.remove(zip_filename)
shutil.rmtree(DUMP_DIR)
print(f"Local backup files cleaned up: {zip_filename} and {DUMP_DIR}")

# Step 4: Delete old backups, keep only last 3
backup_pattern = re.compile(r"backup_(\\d{4}-\\d{2}-\\d{2})\\.zip")
files = ftp.nlst()
backups = []
for fname in files:
    m = backup_pattern.match(fname)
    if m:
        backups.append((fname, m.group(1)))
backups.sort(key=lambda x: x[1], reverse=True)
for old in backups[3:]:
    ftp.delete(old[0])

ftp.quit()

print(f"Backup complete: {zip_filename} uploaded to FTP and old backups cleaned.")
