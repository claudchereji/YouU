import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
import re
import time

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouU")
        
        # Set the icon for the application
        # root.iconbitmap(default='icon.icns')

        # Create and pack a label
        label_text = "Welcome to YouU! Glad you could attend!\nPlease enter the folder name and YouTube URL below to get started"
        label = tk.Label(root, text=label_text, wraplength=300)  # Adjust wraplength as needed
        label.pack(pady=10)


        # Create and pack a label for folder name
        folder_label = tk.Label(root, text="Folder Name:")
        folder_label.pack(pady=5)

        # Create and pack an entry for folder name
        self.folder_name_var = tk.StringVar()
        folder_name_entry = tk.Entry(root, textvariable=self.folder_name_var, width=30)
        folder_name_entry.pack(pady=5)

        # Create and pack a label for YouTube URL
        url_label = tk.Label(root, text="YouTube URL:")
        url_label.pack(pady=5)

        # Create and pack an entry for YouTube URL
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(root, textvariable=self.url_var, width=30)
        url_entry.pack(pady=5)

        # Create and pack a progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(root, variable=self.progress_var, mode="determinate")
        progress_bar.pack(pady=10)

        # Create and pack a label for debug information
        self.debug_label = tk.Label(root, text="")
        self.debug_label.pack(pady=5)

        # Create and pack a label for progress
        self.progress_label = tk.Label(root, text="Progress: N/A")
        self.progress_label.pack(pady=5)

        # Create and pack a button to start the process
        start_button = tk.Button(root, text="Start", command=self.start_process)
        start_button.pack(pady=10)

        # Create and pack a button to restart the application
        restart_button = tk.Button(root, text="Restart", command=self.restart_app)
        restart_button.pack(pady=10)

    def update_progress(self, output_queue):
        start_time = time.time()
        total_items = None
        current_item = None
        converting_text_shown = False  # Flag to check if converting text has been shown

        while True:
            try:
                line = output_queue.get_nowait()
                print("Output Line:", line)  # Debugging line to see the actual output

                # Parse the output to determine progress (customize as needed)
                if "Downloading item" in line:
                    # Extract current item and total items from the line
                    match = re.search(r'Downloading item (\d+) of (\d+)', line)
                    if match:
                        current_item, total_items = map(int, match.groups())

                        # Update progress label dynamically
                        self.progress_label.config(text=f"Progress: {current_item} of {total_items}")

                elif "%" in line and total_items is not None and current_item is not None:
                    try:
                        progress_percent = int(line.split("%")[0].split()[-1])
                        self.progress_var.set(progress_percent)

                        # Update progress based on current item and total items
                        self.progress_var.set((current_item / total_items) * progress_percent)

                    except ValueError:
                        pass

                elif "Converting subtitles to text..." in line or "Converting subtitles to Markdown..." in line:
                    # Display converting text only once
                    if not converting_text_shown:
                        self.debug_label.config(text=line.strip())
                        converting_text_shown = True

                elif "Subtitles processed successfully." in line:
                    # Display final output persistently
                    self.debug_label.config(text=line.strip())

            except queue.Empty:
                pass
            self.root.update_idletasks()

    def format_time(self, seconds):
        # Format seconds into HH:MM:SS
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "{:02}:{:02}:{:02}".format(int(h), int(m), int(s))

    def run_process(self, output_queue):
        folder_name = self.folder_name_var.get()
        youtube_url = self.url_var.get()

        bash_script_content = f"""#!/bin/bash

folder_name="{folder_name}"

mkdir "$folder_name"

url="{youtube_url}"

yt-dlp --write-auto-subs --default-search "ytsearch" --skip-download "$url" 2>&1
yt_dlp_status=$?

if [ $yt_dlp_status -eq 0 ]; then
    find . -name "*.vtt" -exec python3 vtt2text.py {{}} \; &&
    echo "Converting subtitles to text..." && 
    rm *.vtt && 
    find . -iname "*.txt" -exec bash -c 'mv "$0" "${{0%\.txt}}.md"' {{}} \; &&
    echo "Converting subtitles to Markdown..." &&
    python3 markDownScript.py
    bash appender.sh
    mv *.md "$folder_name"/

    echo "Subtitles processed successfully."
    echo "Files moved to $folder_name."
else
    echo "yt-dlp command failed with status $yt_dlp_status."
fi
"""

        with open("temp_script.sh", "w") as temp_file:
            temp_file.write(bash_script_content)

        process = subprocess.Popen(["bash", "temp_script.sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            output_queue.put(line)

        process.communicate()
        subprocess.run(["rm", "temp_script.sh"])

    def start_process(self):
        output_queue = queue.Queue()
        progress_thread = threading.Thread(target=self.update_progress, args=(output_queue,), daemon=True)
        progress_thread.start()

        process_thread = threading.Thread(target=self.run_process, args=(output_queue,), daemon=True)
        process_thread.start()

        self.progress_var.set(0)
        self.progress_var.trace("w", lambda *args: self.root.update_idletasks())

    def restart_app(self):
        # Reset labels when restart button is clicked
        self.folder_name_var.set("")  # Clear the folder name entry
        self.url_var.set("")  # Clear the YouTube URL entry
        self.progress_label.config(text="Progress: N/A")
        self.debug_label.config(text="")
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()
