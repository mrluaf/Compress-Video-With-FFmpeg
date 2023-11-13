import tkinter as tk
from tkinter import filedialog
import subprocess
from tkinter import scrolledtext
from tkinter import ttk
import threading
import re
import os
from send2trash import send2trash
from moviepy.editor import VideoFileClip
from tkinter import messagebox  # Import the messagebox module

# Function to center the window on the screen
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# Function to get the user's "Downloads" folder on Windows
def get_downloads_folder():
    return os.path.expanduser("~\Downloads")

# Function to get file information
def get_file_info(input_file):
    file_info = {}
    if os.path.exists(input_file):
        filename = os.path.basename(input_file)
        file_info['File name'] = filename
        file_size = os.path.getsize(input_file) / (1024 * 1024)  # Size in MB
        file_info['File size'] = f"{file_size:.2f} MB"
        video_clip = VideoFileClip(input_file)
        video_duration = video_clip.duration
        video_duration_str = f"{int(video_duration/3600):02}:{int((video_duration%3600)/60):02}:{int(video_duration%60):02}"
        file_info['Video len'] = video_duration_str
    return file_info

# Function to update file information
def update_file_info():
    downloads_folder = get_downloads_folder()
    input_file = filedialog.askopenfilename(title="Select a video file", filetypes=(("Video files", "*.mp4 *.avi *.mkv"), ("All files", "*.*")), initialdir=downloads_folder)
    if input_file:
        file_info = get_file_info(input_file)
        file_info_text.config(state=tk.NORMAL)
        file_info_text.delete(1.0, tk.END)
        for key, value in file_info.items():
            file_info_text.insert(tk.END, f"{key}: {value}\n")
        file_info_text.config(state=tk.DISABLED)
        process_button.config(state=tk.NORMAL)  # Enable the process button
        process_button['command'] = lambda: process_video(input_file)  # Set the process_video function with the selected file

# Function to process the selected video file
def process_video(input_file):
    global stop_processing
    stop_processing = False

    output_prefix = "compressed_"
    filename_without_extension = input_file.split("/")[-1].split(".")[0]
    output_file = os.path.normpath(os.path.join(os.path.dirname(input_file), f"{output_prefix}{filename_without_extension}.mp4"))

    # Check if the output file already exists
    if os.path.exists(output_file):
        confirm = messagebox.askyesno("Overwrite Confirmation", f"{output_file} already exists. Overwrite?")
        if not confirm:
            return  # Stop processing if not confirmed

        # Move the existing output file to the recycle bin
        send2trash(output_file)

    command = f'ffmpeg -i "{input_file}" -vf "scale=iw/3:ih/3" -c:v libx264 -crf 23 -c:a aac -b:a 192k "{output_file}"'

    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, f"Processing: {input_file}\n")
    log_text.insert(tk.END, f"Command: {command}\n\n")
    log_text.config(state=tk.DISABLED)

    progress_bar["value"] = 0
    percentage_label.config(text="0%")

    def update_progress():
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = None
            while not stop_processing:
                if process.poll() is not None:  # Process has finished
                    break

                line = process.stderr.readline()
                if not line:
                    break
                match = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", line)
                if match:
                    duration = match.group(1)
                match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                if match and duration:
                    current_time = match.group(1)
                    time_percentage = 100 * (time_to_seconds(current_time) / time_to_seconds(duration))
                    progress_bar["value"] = time_percentage
                    percentage_label.config(text=f"{int(time_percentage)}%")
                log_text.config(state=tk.NORMAL)
                log_text.insert(tk.END, line)
                log_text.config(state=tk.DISABLED)
                log_text.see(tk.END)
                window.update_idletasks()

            if not stop_processing:
                progress_bar["value"] = 100
                percentage_label.config(text="100%")
                
                # Show a completion message
                messagebox.showinfo("Video Processing Complete", "Video processing has been completed.")
                
            else:
                pass  # Remove the alert here
        except subprocess.CalledProcessError as e:
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"Error: {e}\n")
            log_text.config(state=tk.DISABLED)
            if not stop_processing:
                pass  # Remove the alert here

    # Create a new thread for FFmpeg processing
    processing_thread = threading.Thread(target=update_progress)
    processing_thread.start()

# Function to convert time to seconds
def time_to_seconds(time_str):
    h, m, s = map(float, time_str.split(':'))
    return h * 3600 + m * 60 + s

# Function to handle the window close event
def on_closing():
    global stop_processing
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        stop_processing = True
        window.destroy()

# Create the main window
window = tk.Tk()
window.title("Video Processing with FFmpeg")

# Determine the window width and height based on the monitor's resolution
window_width = 800  # You can adjust this as needed
window_height = 600  # You can adjust this as needed

# Center the main window on the screen
center_window(window, window_width, window_height)

# Bind the window's close event to the on_closing function
window.protocol("WM_DELETE_WINDOW", on_closing)

# Create a frame for file information
file_info_frame = tk.Frame(window)
file_info_frame.pack(pady=10)
file_info_text = tk.Text(file_info_frame, height=5, width=70, state=tk.DISABLED)  # Updated width to 70
file_info_text.pack()

# Create a button to update file information
update_file_info_button = tk.Button(window, text="Update File Info", command=update_file_info)
update_file_info_button.pack(pady=10)

# Create a frame for the log
log_frame = tk.Frame(window)
log_frame.pack(pady=10)
log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70, state=tk.DISABLED)  # Updated width to 70
log_text.pack()

# Create a progress bar
progress_frame = tk.Frame(window)
progress_frame.pack(pady=10)
progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=200, mode="determinate")
progress_bar.grid(row=0, column=0)
percentage_label = tk.Label(progress_frame, text="0%")
percentage_label.grid(row=0, column=1)

# Create a button to process the video (this will be updated when a file is selected)
process_button = tk.Button(window, text="Process Video", state=tk.DISABLED)
process_button.pack(pady=10)

# Create an exit button
exit_button = tk.Button(window, text="Exit", command=on_closing)
exit_button.pack()

window.mainloop()
