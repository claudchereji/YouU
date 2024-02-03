#!/bin/bash

# Ask user for a folder name
read -p "Enter folder name: " folder_name

# Create the folder
mkdir "$folder_name"

# Ask user for a YouTube URL
read -p "Enter YouTube URL: " url

# Download subtitles
yt-dlp --write-auto-subs --default-search "ytsearch" --skip-download "$url"
yt_dlp_status=$?

if [ $yt_dlp_status -eq 0 ]; then
    # Process subtitles
    find . -name "*.vtt" -exec python3 vtt2text.py {} \; && 
    rm *.vtt && 
    find . -iname "*.txt" -exec bash -c 'mv "$0" "${0%\.txt}.md"' {} \; &&
    
    # Run additional script
    python3 markDownScript.py

    # Move .md files to the created folder
    mv *.md "$folder_name"/

    # Debug information
    echo "Subtitles processed successfully."
    echo "Files moved to $folder_name."
else
    echo "yt-dlp command failed with status $yt_dlp_status."
fi
