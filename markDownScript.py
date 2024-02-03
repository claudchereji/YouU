import os
import re

def extract_video_id_from_filename(filename):
    # Extract video ID from the filename enclosed in square brackets
    match = re.search(r'\[([^\]]+)\]', filename)
    return match.group(1) if match else None

def convert_markdown_time_to_youtube_format(markdown_time):
    # Convert markdown time format (01:23) to YouTube time format (t=1h23m)
    hours, minutes = map(int, markdown_time.split(':'))
    return f't={hours}h{minutes}m'

def generate_youtube_link(video_id, timestamp):
    # Construct YouTube link with the given video ID and timestamp
    return f'https://www.youtube.com/watch?v={video_id}&{timestamp}'

def process_markdown_file(file_path):
    # Extract the filename from the path
    filename = os.path.basename(file_path)

    video_id = extract_video_id_from_filename(filename)

    if video_id:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Extract time codes and replace them with YouTube links
        content = re.sub(r'(\d+:\d+)', lambda match: generate_youtube_link(video_id, convert_markdown_time_to_youtube_format(match.group(0))), content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Successfully processed {file_path}')
    else:
        print(f'Video ID not found in the filename of {file_path}')

def process_all_markdown_files():
    # Get the directory of the script
    script_directory = os.path.dirname(__file__)

    # Iterate through all files in the directory
    for filename in os.listdir(script_directory):
        if filename.endswith('.md'):
            file_path = os.path.join(script_directory, filename)
            process_markdown_file(file_path)

# Run the script to process all Markdown files in the script's directory
process_all_markdown_files()
