import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import threading
import queue
import re
import time
import os
import glob
import shutil


class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouU")

        # Create and pack a label
        label_text = (
            "Welcome to YouU! Glad you could attend!\n"
            "Please select a folder and enter the YouTube URL below to get started"
        )
        label = tk.Label(root, text=label_text, wraplength=300)
        label.pack(pady=10)

        # Create and pack a frame for folder selection
        folder_frame = tk.Frame(root)
        folder_frame.pack(pady=5)

        # Create and pack a label for folder selection
        folder_label = tk.Label(folder_frame, text="Selected Folder:")
        folder_label.pack(side=tk.LEFT, padx=5)

        # Create and pack a label to display the selected folder path
        self.folder_path_var = tk.StringVar()
        self.folder_path_label = tk.Label(
            folder_frame,
            textvariable=self.folder_path_var,
            width=30,
            anchor="w",
            relief="sunken",
        )
        self.folder_path_label.pack(side=tk.LEFT, padx=5)

        # Create and pack a button to select folder
        select_folder_button = tk.Button(
            folder_frame, text="Browse...", command=self.select_folder
        )
        select_folder_button.pack(side=tk.LEFT, padx=5)

        # Create and pack a label for YouTube URL
        url_label = tk.Label(root, text="YouTube URL:")
        url_label.pack(pady=5)

        # Create and pack an entry for YouTube URL
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(root, textvariable=self.url_var, width=30)
        url_entry.pack(pady=5)

        # Create and pack a progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            root, variable=self.progress_var, mode="determinate"
        )
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

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder to Export Files")
        if folder_path:
            self.folder_path_var.set(folder_path)

    def update_progress(self, output_queue):
        total_items = None
        current_item = None
        converting_text_shown = False

        while True:
            try:
                line = output_queue.get_nowait()
                print("Output Line:", line)

                if "Downloading item" in line:
                    match = re.search(r"Downloading item (\d+) of (\d+)", line)
                    if match:
                        current_item, total_items = map(int, match.groups())
                        self.progress_label.config(
                            text=f"Progress: {current_item} of {total_items}"
                        )

                elif (
                    "%" in line and total_items is not None and current_item is not None
                ):
                    try:
                        progress_percent = int(line.split("%")[0].split()[-1])
                        self.progress_var.set(
                            (current_item / total_items) * progress_percent
                        )
                    except ValueError:
                        pass

                elif (
                    "Converting subtitles to text..." in line
                    or "Converting subtitles to Markdown..." in line
                ):
                    if not converting_text_shown:
                        self.debug_label.config(text=line.strip())
                        converting_text_shown = True

                elif "Subtitles processed successfully." in line:
                    self.debug_label.config(text=line.strip())

            except queue.Empty:
                pass
            self.root.update_idletasks()

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "{:02}:{:02}:{:02}".format(int(h), int(m), int(s))

    def append_sections_to_markdown(self, folder_path):
        """Replaces appender.sh: Adds section headers to Markdown files."""
        for file in glob.glob(os.path.join(folder_path, "*.md")):
            section_number = 1
            temp_file = file + ".tmp"
            with open(file, "r", encoding="utf-8") as f_in, open(
                temp_file, "w", encoding="utf-8"
            ) as f_out:
                for line in f_in:
                    if line.strip().startswith("https://"):
                        f_out.write(f"\n## Section {section_number}\n")
                        section_number += 1
                    f_out.write(line)
            os.replace(temp_file, file)
        print("Section numbers added to all markdown files.")

    def run_process(self, output_queue):
        folder_path = self.folder_path_var.get()
        youtube_url = self.url_var.get()

        if not folder_path:
            self.debug_label.config(text="Please select a folder.")
            return

        if not youtube_url:
            self.debug_label.config(text="Please enter a YouTube URL.")
            return

        try:
            # Run yt-dlp to download subtitles
            output_queue.put("Downloading subtitles...")
            process = subprocess.Popen(
                [
                    "yt-dlp",
                    "--write-auto-subs",
                    "--default-search",
                    "ytsearch",
                    "--skip-download",
                    youtube_url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in process.stdout:
                output_queue.put(line)
            process.communicate()
            if process.returncode != 0:
                output_queue.put(
                    f"yt-dlp command failed with status {process.returncode}."
                )
                self.debug_label.config(text="Failed to download subtitles.")
                return

            # Process .vtt files
            output_queue.put("Converting subtitles to text...")
            for vtt_file in glob.glob("*.vtt"):
                subprocess.run([sys.executable, "vtt2text.py", vtt_file], check=True)
                os.remove(vtt_file)

            # Rename .txt to .md
            for txt_file in glob.glob("*.txt"):
                md_file = os.path.splitext(txt_file)[0] + ".md"
                os.rename(txt_file, md_file)

            # Process Markdown files
            output_queue.put("Converting subtitles to Markdown...")
            subprocess.run([sys.executable, "markDownScript.py"], check=True)

            # Append section headers
            self.append_sections_to_markdown(".")

            # Move .md files to the selected folder
            for md_file in glob.glob("*.md"):
                shutil.move(
                    md_file, os.path.join(folder_path, os.path.basename(md_file))
                )

            output_queue.put("Subtitles processed successfully.")
            output_queue.put(f"Files moved to {folder_path}.")
            self.debug_label.config(text="Subtitles processed successfully.")

        except Exception as e:
            output_queue.put(f"Error: {str(e)}")
            self.debug_label.config(text=f"Error: {str(e)}")

    def start_process(self):
        output_queue = queue.Queue()
        progress_thread = threading.Thread(
            target=self.update_progress, args=(output_queue,), daemon=True
        )
        progress_thread.start()

        process_thread = threading.Thread(
            target=self.run_process, args=(output_queue,), daemon=True
        )
        process_thread.start()

        self.progress_var.set(0)
        self.progress_var.trace("w", lambda *args: self.root.update_idletasks())

    def restart_app(self):
        self.folder_path_var.set("")
        self.url_var.set("")
        self.progress_label.config(text="Progress: N/A")
        self.debug_label.config(text="")
        self.root.update_idletasks()


if __name__ == "__main__":
    import sys

    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()
