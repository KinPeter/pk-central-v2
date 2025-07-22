#!/bin/bash
export MONGODB_URI="your_mongodb_uri"
export FTP_HOST="your_ftp_host"
export FTP_USER="your_ftp_user"
export FTP_PASS="your_ftp_pass"

python3 /path/to/central-v2/backup/backup.py