#!/bin/bash
# Download backup archive on device

ARCHIVE_URL="http://localhost:8888/backup_data_no_apks.tar.gz"
ARCHIVE_NAME="$(basename $ARCHIVE_URL)"
EXPECTED_MD5="2401e59b03cf94cdbb950900da48860e"

echo "[*] Downloading backup from $ARCHIVE_URL"
wget -q "$ARCHIVE_URL" -O "/data/local/tmp/$ARCHIVE_NAME" || exit 1

if [ ! -z "$EXPECTED_MD5" ]; then
    echo "[*] Verifying checksum..."
    ACTUAL_MD5=$(md5sum "/data/local/tmp/$ARCHIVE_NAME" | cut -d' ' -f1)
    if [ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]; then
        echo "[!] Checksum mismatch! Expected: $EXPECTED_MD5, Got: $ACTUAL_MD5"
        exit 1
    fi
    echo "[✓] Checksum OK"
fi

echo "[✓] Download complete: /data/local/tmp/$ARCHIVE_NAME"
echo "[*] Extract with: tar xzf /data/local/tmp/$ARCHIVE_NAME"
