import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
from yt_dlp.utils import download_range_func
import os
import threading
import re
import subprocess
import sys
from tkinterdnd2 import DND_FILES, TkinterDnD
import shutil
import tempfile
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VideoDownloader:
    QUALITY_OPTIONS = {
        "Best Quality (Auto)": "(bv+ba/b)[vcodec!*=av01]",
        "2160p 4K": "(bv[height<=2160]+ba/b)[vcodec!*=av01]",
        "1440p": "(bv[height<=1440]+ba/b)[vcodec!*=av01]",
        "1080p FHD": "(bv[height<=1080]+ba/b)[vcodec!*=av01]",
        "720p HD": "(bv[height<=720]+ba/b)[vcodec!*=av01]",
        "480p SD": "(bv[height<=480]+ba/b)[vcodec!*=av01]",
        "360p SD": "(bv[height<=360]+ba/b)[vcodec!*=av01]",
        "Audio Only": "bestaudio/best",
        "Worst (Smallest)": "worst[vcodec!*=av01]"
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("950x700")
        self.root.configure(bg='#232323')
        
        # Variables
        self.download_progress = tk.DoubleVar()
        self.progress_text = tk.StringVar(value="Ready to download...")
        self.instructions_visible = tk.BooleanVar(value=False)
        self.current_file = None
        self.selected_quality = tk.StringVar(value="Best Quality (Auto)")
        
        self.setup_ui()
        self.setup_drag_drop()
        
    def setup_ui(self):
        # Create main container with scrollable canvas
        main_container = tk.Frame(self.root, bg='#232323')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for scrollable content
        self.main_canvas = tk.Canvas(main_container, bg='#232323', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg='#232323')
        
        # Configure scrollable frame
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Main content frame with padding
        content_frame = tk.Frame(self.scrollable_frame, bg='#232323', padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo
        header_frame = tk.Frame(content_frame, bg='#232323')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Logo and title container 
        logo_title_frame = tk.Frame(header_frame, bg='#232323', height=130) 
        logo_title_frame.pack(fill=tk.X)
        logo_title_frame.pack_propagate(False) 
        self.load_logo(logo_title_frame)
        
        # Instructions section
        self.create_instructions_section(content_frame)
        
        # Video URL section
        self.create_url_section(content_frame)
        
        # Drag and drop section
        self.create_drag_drop_section(content_frame)
        
        # Clip download section
        self.create_clip_section(content_frame)
        
        # Progress section
        self.create_progress_section()
    
    def load_logo(self, parent):
        """Load and display logo at top left with title below - FIXED FOR BUNDLED APPS"""
        try:
            from PIL import Image, ImageTk
            
            logo_files = ["logo.png"]
            logo_loaded = False
            
            for logo_file in logo_files:
                # Use resource_path for proper bundled app support
                logo_path = resource_path(logo_file)
                if os.path.exists(logo_path):
                    try:
                        logo_image = Image.open(logo_path)
                        self.logo_photo = ImageTk.PhotoImage(logo_image)
                        
                        logo_label = tk.Label(parent, 
                                            image=self.logo_photo, 
                                            bg='#232323')
                        logo_label.pack(side=tk.TOP, anchor='w', padx=10, pady=(10, 5))
                        
                        logo_loaded = True
                        print(f"Logo loaded successfully: {logo_file}")
                        break
                        
                    except Exception as e:
                        print(f"Could not load {logo_file}: {e}")
                        continue
            
            if not logo_loaded:
                print("No logo file found or loaded")
                # Create a text placeholder if logo fails
                placeholder = tk.Label(parent, text="[LOGO]", 
                                     font=('Arial', 16, 'bold'),
                                     fg='#888888', bg='#232323')
                placeholder.pack(side=tk.TOP, anchor='w', padx=10, pady=(10, 5))
                
        except ImportError:
            print("PIL (Pillow) not installed")
            # Fallback placeholder
            placeholder = tk.Label(parent, text="[LOGO]", 
                                 font=('Arial', 16, 'bold'),
                                 fg='#888888', bg='#232323')
            placeholder.pack(side=tk.TOP, anchor='w', padx=10, pady=(10, 5))
        
        title_label = tk.Label(parent, 
                             text="Video Downloader", 
                             font=('Arial', 18, 'bold'),
                             fg='#f2f2f2', 
                             bg='#232323')
        title_label.pack(side=tk.TOP, anchor='w', padx=10, pady=(20, 10))
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def add_hover_effect(self, widget, normal_bg, normal_fg, hover_bg, hover_fg):
        """Add hover effect to widgets"""
        def on_enter(e):
            widget.config(bg=hover_bg, fg=hover_fg)
        def on_leave(e):
            widget.config(bg=normal_bg, fg=normal_fg)
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def create_instructions_section(self, parent):
        # Instructions container
        instructions_container = tk.Frame(parent, bg='#393838', pady=5)
        instructions_container.pack(fill=tk.X, pady=(0, 20))
        
        # Instructions header
        instructions_header = tk.Frame(instructions_container, bg='#393838', height=50)
        instructions_header.pack(fill=tk.X, padx=10, pady=5)
        instructions_header.pack_propagate(False)
        
        # Instructions text
        instructions_text = tk.Label(instructions_header, 
                                   text="Instructions",
                                   font=('Arial', 13, 'bold'),
                                   fg='#f2f2f2', bg='#393838')
        instructions_text.pack(side=tk.LEFT, padx=(15, 0), pady=12)
        
        # Toggle button
        self.instructions_btn = tk.Button(instructions_header, 
                                         text="+",
                                         font=('Arial', 16, 'bold'),
                                         bg='#393838', fg='#f2f2f2',
                                         activebackground='#f2f2f2', activeforeground='#232323',
                                         border=0, width=3, height=1,
                                         relief=tk.FLAT,
                                         command=self.toggle_instructions)
        self.instructions_btn.pack(side=tk.RIGHT, padx=(0, 15), pady=8)
        self.add_hover_effect(self.instructions_btn, '#393838', '#f2f2f2', '#f2f2f2', '#232323')
        
        # Make header clickable
        def header_click(event):
            self.toggle_instructions()
        
        instructions_header.bind('<Button-1>', header_click)
        instructions_text.bind('<Button-1>', header_click)
        
        # Instructions content
        self.instructions_frame = tk.Frame(instructions_container, bg='#393838')
        
        instructions_text_content = """HOW TO USE THIS VIDEO DOWNLOADER:

     DOWNLOAD FULL VIDEOS:
   • Paste any YouTube or Google Drive video URL in the "Video URL" field
   • Select desired quality from the dropdown (Best Quality, 1080p, 720p, etc.)
   • Click the red "Download Full Video" button
   • Choose where to save the video on your computer
   • Wait for download to complete

     CREATE VIDEO CLIPS:
   • Method 1 - From URLs: Enter YouTube/Google Drive URL + set start/end times + quality
   • Method 2 - From Local Files: Drag & drop a video file from your computer
   • Set start time using the hour:minute:second spinboxes (e.g., 0:1:30 = 1 min 30 sec)
   • Set end time (must be later than start time)
   • Select quality for online clips
   • Click "Download Clip" button
   • Choose where to save the clip

     DRAG & DROP FEATURE:
   • Simply drag any video file from your computer into the upload area
   • Or click the upload area to browse and select a video file
   • Supported formats: MP4, AVI, MKV, MOV, WMV, FLV, WebM

     TIME FORMAT EXAMPLES:
   • 0:0:30 = 30 seconds
   • 0:2:15 = 2 minutes 15 seconds  
   • 1:30:0 = 1 hour 30 minutes
   • Use the spinbox arrows or type directly

     QUALITY OPTIONS:
   • Best Quality (Auto) - Highest available quality with AAC audio
   • 2160p 4K - Ultra HD (when available)
   • 1440p - 2K quality
   • 1080p FHD - Full HD
   • 720p HD - HD quality (Opus audio automatically converted to AAC)
   • 480p SD - Standard definition
   • 360p SD - Lower quality, smaller file
   • Audio Only - Extract audio track only
   • Worst (Smallest) - Lowest quality, smallest file size
   • Note: AV1 codec excluded, all audio converted to AAC for universal playback

     FILE NAMING:
   • Videos saved with unique timestamped names to prevent overwrites
   • Format: "Video Title_TIMESTAMP.mp4"
   • Each download gets a guaranteed unique filename

     SUPPORTED WEBSITES:
   • YouTube (all video types)
   • Google Drive (shared video links)
   • Many other video sites supported by yt-dlp

     TIPS:
   • Make sure you have a stable internet connection for downloads
   • Higher qualities take longer to download and use more storage
   • Downloads are optimized for speed with concurrent fragments
   • All audio is automatically converted to AAC format for universal compatibility
   • Multiple downloads to same folder won't overwrite each other
   • Check the progress bar at the bottom for download status
   • Local video processing is much faster than downloading clips from URLs
   • The app works offline for local video file processing

     ADVANCED FEATURES:
   • Automatic retry on failed downloads
   • Concurrent fragment downloading for faster speeds
   • Smart quality selection based on availability
   • Automatic audio codec conversion for compatibility
   • Unique filename generation to prevent overwrites
   • Support for both online streaming and local video processing
   • Real-time progress tracking with detailed status updates

     FILE MANAGEMENT:
   • All downloads include timestamp in filename
   • Automatic duplicate prevention
   • Smart output directory selection
   • Progress tracking for all operations
   • Error logging and recovery options"""
        
        # Simple label for instructions
        instructions_label = tk.Label(self.instructions_frame, 
                                    text=instructions_text_content,
                                    font=('Arial', 9),
                                    fg='#f2f2f2', bg='#393838',
                                    justify=tk.LEFT, anchor='nw')
        instructions_label.pack(fill='both', padx=20, pady=15)
        
    def toggle_instructions(self):
        """Toggle instructions visibility"""
        if self.instructions_visible.get():
            # Hide instructions
            self.instructions_frame.pack_forget()
            self.instructions_btn.config(text="+")
            self.instructions_visible.set(False)
        else:
            # Show instructions
            self.instructions_frame.pack(fill=tk.X, pady=(5, 10))
            self.instructions_btn.config(text="−")
            self.instructions_visible.set(True)
            
    def create_url_section(self, parent):
        # Video URL section
        url_outer_frame = tk.Frame(parent, bg='#232323')
        url_outer_frame.pack(fill=tk.X, pady=(0, 20))
        
        url_frame = tk.Frame(url_outer_frame, bg='#232323', pady=10, padx=5)
        url_frame.pack(anchor='center')
        
        url_label = tk.Label(url_frame, text="Video URL", 
                            font=('Arial', 12, 'bold'), 
                            fg='#f2f2f2', bg='#232323')
        url_label.pack(anchor=tk.W, pady=(0, 10))
        
        # URL input frame
        url_input_frame = tk.Frame(url_frame, bg='#232323')
        url_input_frame.pack()
        
        self.url_entry = tk.Entry(url_input_frame, 
                                 font=('Arial', 11), width=50,
                                 bg='#393838', fg='#f2f2f2',
                                 insertbackground='#f2f2f2',
                                 relief=tk.FLAT, bd=0)
        self.url_entry.pack(side=tk.LEFT, ipady=10, padx=(0, 10))
        self.url_entry.insert(0, "Enter video URL...")
        self.url_entry.bind('<FocusIn>', self.clear_placeholder)
        
        # Quality dropdown
        quality_label = tk.Label(url_input_frame, text="Quality:", 
                                font=('Arial', 11), fg='#f2f2f2', bg='#232323')
        quality_label.pack(side=tk.LEFT, padx=(10, 5))
        
        self.quality_dropdown = ttk.Combobox(url_input_frame, 
                                           width=18, 
                                           font=('Arial', 10),
                                           textvariable=self.selected_quality,
                                           state="readonly",
                                           values=list(self.QUALITY_OPTIONS.keys()))
        self.quality_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.quality_dropdown.current(0)
        
        # Download button
        download_btn = tk.Button(url_input_frame, 
                               text="Download Full Video",
                               font=('Arial', 11, 'bold'),
                               bg='#ff3000', fg='#f2f2f2',
                               activebackground='#f2f2f2', activeforeground='#232323',
                               border=0, padx=20, pady=10,
                               relief=tk.FLAT,
                               command=self.download_full_video)
        download_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.add_hover_effect(download_btn, '#ff3000', '#f2f2f2', '#f2f2f2', '#232323')
        
    def create_drag_drop_section(self, parent):
        # Drag and drop section
        drop_outer_frame = tk.Frame(parent, bg='#232323')
        drop_outer_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Center the drop content
        drop_frame = tk.Frame(drop_outer_frame, bg='#232323', pady=10, padx=5)
        drop_frame.pack(anchor='center')
        
        # Canvas for drag-drop area
        canvas_height = 220
        self.drop_canvas = tk.Canvas(drop_frame, 
                                   bg='#232323',
                                   highlightthickness=0,
                                   height=canvas_height, width=600) 
        self.drop_canvas.pack()
        
        # Draw dotted border
        self.drop_canvas.bind('<Configure>', self.draw_dotted_border)
        
        # Content frame
        content_frame = tk.Frame(self.drop_canvas, bg='#232323')
        
        # Upload icon and text
        upload_icon = tk.Label(content_frame, text="⬆", 
                             font=('Arial', 32), fg='#f2f2f2', bg='#232323')
        upload_icon.pack(pady=(10, 5))
        
        drop_label = tk.Label(content_frame, 
                             text="Click or drag files here to upload",
                             font=('Arial', 12), fg='#f2f2f2', bg='#232323')
        drop_label.pack(pady=(0, 10))
        
        # Center the content in canvas
        self.content_window = self.drop_canvas.create_window(300, 110, window=content_frame) 
        
        self.drop_area = content_frame
        
        # Bind events
        content_frame.bind('<Button-1>', self.browse_local_file)
        upload_icon.bind('<Button-1>', self.browse_local_file)
        drop_label.bind('<Button-1>', self.browse_local_file)
        self.drop_canvas.bind('<Button-1>', self.browse_local_file)
        
        # File info label
        self.file_info = tk.Label(drop_frame, text="", 
                                 font=('Arial', 10), fg='#f2f2f2', bg='#232323')
        self.file_info.pack(pady=(10, 0))
        
    def draw_dotted_border(self, event=None):
        # Clear previous drawings
        self.drop_canvas.delete("border")
        
        # Get canvas dimensions
        width = self.drop_canvas.winfo_width()
        height = self.drop_canvas.winfo_height()
        
        if width > 1 and height > 1:
            # Draw dotted border rectangle
            self.drop_canvas.create_rectangle(10, 10, width-10, height-10,
                                            outline='#f2f2f2',
                                            width=2,
                                            dash=(5, 5),
                                            tags="border")
    
    def create_clip_section(self, parent):
        # Clip section
        clip_outer_frame = tk.Frame(parent, bg='#232323')
        clip_outer_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Center the clip content
        clip_frame = tk.Frame(clip_outer_frame, bg='#232323', pady=10, padx=5)
        clip_frame.pack(anchor='center')  
        
        clip_label = tk.Label(clip_frame, text="Clip Download", 
                             font=('Arial', 12, 'bold'), 
                             fg='#f2f2f2', bg='#232323')
        clip_label.pack(anchor=tk.W, pady=(0, 10)) 
        
        # Time inputs container 
        time_frame = tk.Frame(clip_frame, bg='#232323')
        time_frame.pack(pady=(0, 15))
        
        # Start time section
        start_frame = tk.Frame(time_frame, bg='#232323')
        start_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        start_label = tk.Label(start_frame, text="Start Time", 
                              font=('Arial', 11, 'bold'), fg='#f2f2f2', bg='#232323')
        start_label.pack(anchor=tk.W, pady=(0, 8))
        
        start_container = tk.Frame(start_frame, bg='#393838', pady=8, padx=8)
        start_container.pack(pady=(0, 5))
        
        start_input_frame = tk.Frame(start_container, bg='#393838')
        start_input_frame.pack()
        
        # Hours
        tk.Label(start_input_frame, text="Hours", font=('Arial', 8), 
                fg='#f2f2f2', bg='#393838').grid(row=0, column=0, padx=(0, 5))
        self.start_hour = tk.Spinbox(start_input_frame, from_=0, to=23, width=4,
                                    font=('Arial', 11, 'bold'), format='%02.0f',
                                    bg='#393838', fg='#f2f2f2',
                                    buttonbackground='#f2f2f2',
                                    relief=tk.FLAT, bd=0,
                                    justify=tk.CENTER)
        self.start_hour.grid(row=1, column=0, padx=(0, 5))
        self.start_hour.delete(0, tk.END)
        self.start_hour.insert(0, '0')
        
        # Minutes  
        tk.Label(start_input_frame, text="Minutes", font=('Arial', 8),
                fg='#f2f2f2', bg='#393838').grid(row=0, column=1, padx=5)
        self.start_min = tk.Spinbox(start_input_frame, from_=0, to=59, width=4,
                                   font=('Arial', 11, 'bold'), format='%02.0f',
                                   bg='#393838', fg='#f2f2f2',
                                   buttonbackground='#f2f2f2',
                                   relief=tk.FLAT, bd=0,
                                   justify=tk.CENTER)
        self.start_min.grid(row=1, column=1, padx=5)
        self.start_min.delete(0, tk.END)
        self.start_min.insert(0, '0')
        
        # Seconds
        tk.Label(start_input_frame, text="Seconds", font=('Arial', 8),
                fg='#f2f2f2', bg='#393838').grid(row=0, column=2, padx=(5, 0))
        self.start_sec = tk.Spinbox(start_input_frame, from_=0, to=59, width=4,
                                   font=('Arial', 11, 'bold'), format='%02.0f',
                                   bg='#393838', fg='#f2f2f2',
                                   buttonbackground='#f2f2f2',
                                   relief=tk.FLAT, bd=0,
                                   justify=tk.CENTER)
        self.start_sec.grid(row=1, column=2, padx=(5, 0))
        self.start_sec.delete(0, tk.END)
        self.start_sec.insert(0, '0')
        
        # End time section
        end_frame = tk.Frame(time_frame, bg='#232323')
        end_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        end_label = tk.Label(end_frame, text="End Time", 
                            font=('Arial', 11, 'bold'), fg='#f2f2f2', bg='#232323')
        end_label.pack(anchor=tk.W, pady=(0, 8))
        
        end_container = tk.Frame(end_frame, bg='#393838', pady=8, padx=8)
        end_container.pack(pady=(0, 5))
        
        end_input_frame = tk.Frame(end_container, bg='#393838')
        end_input_frame.pack()
        
        # Hours
        tk.Label(end_input_frame, text="Hours", font=('Arial', 8),
                fg='#f2f2f2', bg='#393838').grid(row=0, column=0, padx=(0, 5))
        self.end_hour = tk.Spinbox(end_input_frame, from_=0, to=23, width=4,
                                  font=('Arial', 11, 'bold'), format='%02.0f',
                                  bg='#393838', fg='#f2f2f2',
                                  buttonbackground='#f2f2f2',
                                  relief=tk.FLAT, bd=0,
                                  justify=tk.CENTER)
        self.end_hour.grid(row=1, column=0, padx=(0, 5))
        self.end_hour.delete(0, tk.END)
        self.end_hour.insert(0, '0')
        
        # Minutes
        tk.Label(end_input_frame, text="Minutes", font=('Arial', 8),
                fg='#f2f2f2', bg='#393838').grid(row=0, column=1, padx=5)
        self.end_min = tk.Spinbox(end_input_frame, from_=0, to=59, width=4,
                                 font=('Arial', 11, 'bold'), format='%02.0f',
                                 bg='#393838', fg='#f2f2f2',
                                 buttonbackground='#f2f2f2',
                                 relief=tk.FLAT, bd=0,
                                 justify=tk.CENTER)
        self.end_min.grid(row=1, column=1, padx=5)
        self.end_min.delete(0, tk.END)
        self.end_min.insert(0, '1')
        
        # Seconds
        tk.Label(end_input_frame, text="Seconds", font=('Arial', 8),
                fg='#f2f2f2', bg='#393838').grid(row=0, column=2, padx=(5, 0))
        self.end_sec = tk.Spinbox(end_input_frame, from_=0, to=59, width=4,
                                 font=('Arial', 11, 'bold'), format='%02.0f',
                                 bg='#393838', fg='#f2f2f2',
                                 buttonbackground='#f2f2f2',
                                 relief=tk.FLAT, bd=0,
                                 justify=tk.CENTER)
        self.end_sec.grid(row=1, column=2, padx=(5, 0))
        self.end_sec.delete(0, tk.END)
        self.end_sec.insert(0, '0')
        
        # Quality and button section
        bottom_section = tk.Frame(clip_frame, bg='#232323')
        bottom_section.pack(pady=(0, 10))
        
        # Quality selection
        quality_frame = tk.Frame(bottom_section, bg='#232323')
        quality_frame.pack(pady=(0, 15))
        
        quality_label = tk.Label(quality_frame, text="Quality:", 
                                font=('Arial', 11), fg='#f2f2f2', bg='#232323')
        quality_label.pack(side=tk.LEFT, padx=(0, 5))
        
        quality_dropdown2 = ttk.Combobox(quality_frame, 
                                        width=18, 
                                        font=('Arial', 10),
                                        textvariable=self.selected_quality,
                                        state="readonly",
                                        values=list(self.QUALITY_OPTIONS.keys()))
        quality_dropdown2.pack(side=tk.LEFT)
        
        # Download clip button 
        clip_btn = tk.Button(bottom_section,
                           text="Download Clip",
                           font=('Arial', 11, 'bold'),
                           bg='#ff3000', fg='#f2f2f2',
                           activebackground='#f2f2f2', activeforeground='#232323',
                           border=0, padx=30, pady=10,
                           relief=tk.FLAT,
                           command=self.download_clip)
        clip_btn.pack()
        self.add_hover_effect(clip_btn, '#ff3000', '#f2f2f2', '#f2f2f2', '#232323')
        
    def create_progress_section(self):
        # Progress section 
        progress_container = tk.Frame(self.root, bg='#232323', height=80)
        progress_container.pack(side=tk.BOTTOM, fill=tk.X)
        progress_container.pack_propagate(False)

        # Progress header
        progress_header = tk.Frame(progress_container, bg='#232323')
        progress_header.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.progress_label = tk.Label(progress_header, text="Download Progress (0%)", 
                                      font=('Arial', 12, 'bold'), 
                                      fg='#f2f2f2', bg='#232323')
        self.progress_label.pack(side=tk.LEFT)

        # Close button
        close_btn = tk.Label(progress_header, text="✕", 
                           font=('Arial', 16), fg='#f2f2f2', bg='#232323',
                           cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self.hide_progress())

        # Progress bar
        progress_bar_frame = tk.Frame(progress_container, bg='#232323', height=25)
        progress_bar_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        progress_bar_frame.pack_propagate(False)

        self.progress_bg_frame = tk.Canvas(progress_bar_frame, bg='#393838', height=25, highlightthickness=0)
        self.progress_bg_frame.pack(fill=tk.BOTH, expand=True)
        
        self.progress_width = 0
        self.progress_rect = self.progress_bg_frame.create_rectangle(0, 0, 1, 25, fill='#ff3000', outline='')
        
        # Status text
        self.status_label = tk.Label(progress_container, textvariable=self.progress_text,
                                   font=('Arial', 10), fg='#f2f2f2', bg='#232323')
        self.status_label.pack(anchor=tk.W, padx=20, pady=(0, 10))
        
    def setup_drag_drop(self):
        # Configure drag and drop
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<DropEnter>>', self.on_drop_enter)
        self.drop_area.dnd_bind('<<DropLeave>>', self.on_drop_leave)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop_enter(self, event):
        self.drop_canvas.delete("border")
        width = self.drop_canvas.winfo_width()
        height = self.drop_canvas.winfo_height()
        if width > 1 and height > 1:
            self.drop_canvas.create_rectangle(10, 10, width-10, height-10,
                                            outline='#ff3000',
                                            width=3,
                                            dash=(5, 5),
                                            tags="border")
        
    def on_drop_leave(self, event):
        self.draw_dotted_border()
        
    def on_drop(self, event):
        self.draw_dotted_border()
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0]
            if self.is_video_file(file_path):
                self.current_file = file_path
                filename = os.path.basename(file_path)
                self.file_info.config(text=f"Selected: {filename}", fg='#f2f2f2')
            else:
                messagebox.showerror("Error", "Please drop a video file")
                
    def browse_local_file(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.file_info.config(text=f"Selected: {filename}", fg='#f2f2f2')
            
    def is_video_file(self, file_path):
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        return any(file_path.lower().endswith(ext) for ext in video_extensions)
        
    def clear_placeholder(self, event):
        if self.url_entry.get() == "Enter video URL...":
            self.url_entry.delete(0, tk.END)
            
    def validate_url(self, url):
        # Support YouTube and Google Drive URLs
        youtube_pattern = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        )
        drive_pattern = re.compile(
            r'(https?://)?(drive\.google\.com|docs\.google\.com)'
        )
        return youtube_pattern.match(url) or drive_pattern.match(url)
        
    def get_time_in_seconds(self):
        start_total = int(self.start_hour.get()) * 3600 + int(self.start_min.get()) * 60 + int(self.start_sec.get())
        end_total = int(self.end_hour.get()) * 3600 + int(self.end_min.get()) * 60 + int(self.end_sec.get())
        return start_total, end_total
        
    def update_progress(self, progress_percent):
        # Ensure GUI layout is updated before getting width
        self.progress_bg_frame.update_idletasks()
        canvas_width = self.progress_bg_frame.winfo_width()
        # Fallback if width is zero
        if canvas_width < 2:
            canvas_width = 300
        new_width = max(1, int(canvas_width * (progress_percent / 100)))
        self.progress_bg_frame.coords(self.progress_rect, 0, 0, new_width, 25)
        
        # Updated progress text - shows "Download Complete" when 100%
        if progress_percent >= 100:
            display_text = f"Download Complete ({progress_percent:.1f}%)"
        else:
            display_text = f"Download Progress ({progress_percent:.1f}%)"
        
        self.progress_label.config(text=display_text)
        self.root.update_idletasks()
        
    def hide_progress(self):
        # Reset to minimal size but keep visible
        self.progress_bg_frame.coords(self.progress_rect, 0, 0, 1, 25)
        self.progress_label.config(text="Download Progress (0%)")
        self.progress_text.set("Ready to download...")
        
    def download_full_video(self):
        url = self.url_entry.get().strip()
        if not url or url == "Enter video URL...":
            messagebox.showerror("Error", "Please enter a valid URL")
            return
            
        if not self.validate_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube or Google Drive URL")
            return
            
        save_path = filedialog.askdirectory(title="Select folder to save video")
        if not save_path:
            return
            
        threading.Thread(target=self._download_video, 
                        args=(url, save_path, False), daemon=True).start()
        
    def download_clip(self):
        # Check if we have either URL or local file
        url = self.url_entry.get().strip()
        has_url = url and url != "Enter video URL..." and self.validate_url(url)
        has_file = self.current_file is not None
        
        if not has_url and not has_file:
            messagebox.showerror("Error", "Please enter a URL or select a local video file")
            return
            
        start_time, end_time = self.get_time_in_seconds()
        
        if start_time >= end_time:
            messagebox.showerror("Error", "Start time must be less than end time")
            return
            
        save_path = filedialog.askdirectory(title="Select folder to save clip")
        if not save_path:
            return
            
        if has_file:
            threading.Thread(target=self._process_local_clip, 
                           args=(self.current_file, save_path, start_time, end_time), 
                           daemon=True).start()
        else:
            threading.Thread(target=self._download_video, 
                           args=(url, save_path, True, start_time, end_time), 
                           daemon=True).start()
            
    def _download_video(self, url, save_path, is_clip=False, start_time=None, end_time=None):
        try:
            self.progress_text.set("Starting download..." if not is_clip else f"Downloading clip ({start_time}s to {end_time}s)...")
            
            # Get selected quality format string (AV1-excluded)
            selected_quality = self.selected_quality.get()
            format_string = self.QUALITY_OPTIONS.get(selected_quality, "(bv+ba/b)[vcodec!*=av01]")
            
            # Generate unique filename with timestamp to prevent overwrites
            timestamp = int(time.time())
            
            if is_clip:
                # Unique filename for clips with timestamp
                filename = f"clip_{start_time}s_to_{end_time}s_{timestamp}.%(ext)s"
                ydl_opts = {
                    'format': format_string,
                    'outtmpl': os.path.join(save_path, filename),
                    'download_ranges': download_range_func(None, [(start_time, end_time)]),
                    'force_keyframes_at_cuts': True,
                    'merge_output_format': 'mp4',
                    'concurrent_fragments': 4,
                    'fragment_retries': 10,
                    'retries': 10,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    # Force overwrite to ensure new file is created
                    'overwrites': True,
                    # Force AAC audio codec during merge (fixes 720p Opus issue)
                    'postprocessor_args': {'ffmpeg': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']},
                }
            else:
                # Unique filename for regular downloads with timestamp
                filename = f"%(title)s_{timestamp}.%(ext)s"
                ydl_opts = {
                    'format': format_string,
                    'outtmpl': os.path.join(save_path, filename),
                    'merge_output_format': 'mp4',
                    'concurrent_fragments': 4,
                    'fragment_retries': 10,
                    'retries': 10,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    # Force overwrite to ensure new file is created
                    'overwrites': True,
                    # Force AAC audio codec during merge (fixes 720p Opus issue)
                    'postprocessor_args': {'ffmpeg': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']},
                }
                
            # Add progress hook
            ydl_opts['progress_hooks'] = [self.progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self.progress_text.set("Download completed!")
            self.update_progress(100)
            messagebox.showinfo("Success", f"{'Clip' if is_clip else 'Video'} downloaded successfully in {selected_quality} quality!")
            
        except Exception as e:
            self.progress_text.set("Download failed!")
            messagebox.showerror("Error", f"Download failed: {str(e)}")
            
    def _process_local_clip(self, file_path, save_path, start_time, end_time):
        try:
            self.progress_text.set(f"Processing clip ({start_time}s to {end_time}s)...")
            self.update_progress(50)
            
            # Get FFmpeg path from bundled executable
            ffmpeg_path = self.get_ffmpeg_path()
            if not ffmpeg_path:
                messagebox.showerror("Error", "FFmpeg not found! Please make sure ffmpeg.exe is in the same folder as this app.")
                return
                
            # Generate unique filename for local clips to prevent overwrites
            timestamp = int(time.time())
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            filename = f"{base_name}_clip_{start_time}s_to_{end_time}s_{timestamp}.mp4"
            output_path = os.path.join(save_path, filename)
            
            # Ensure the output path is unique
            counter = 1
            while os.path.exists(output_path):
                filename = f"{base_name}_clip_{start_time}s_to_{end_time}s_{timestamp}_{counter}.mp4"
                output_path = os.path.join(save_path, filename)
                counter += 1
            
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-c:v', 'copy',     
                '-c:a', 'aac',      
                '-b:a', '192k',     
                '-avoid_negative_ts', 'make_zero', 
                output_path,
                '-y'  
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress_text.set("Clip created successfully!")
                self.update_progress(100)
                messagebox.showinfo("Success", f"Clip created successfully!\n\nSaved as: {filename}")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            self.progress_text.set("Processing failed!")
            messagebox.showerror("Error", f"Failed to create clip: {str(e)}")
            
    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            ffmpeg_path = resource_path('ffmpeg.exe')
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path
                
        if os.path.exists('ffmpeg.exe'):
            return os.path.abspath('ffmpeg.exe')
            
        try:
            result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        return None
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.root.after(0, lambda: self.update_progress(progress))
                self.progress_text.set(f"Downloading... {progress:.1f}%")
            elif '_percent_str' in d:
                percent_str = d['_percent_str'].replace('%', '').strip()
                try:
                    progress = float(percent_str)
                    self.root.after(0, lambda: self.update_progress(progress))
                    self.progress_text.set(f"Downloading... {progress:.1f}%")
                except:
                    self.progress_text.set("Downloading...")

def main():
    root = TkinterDnD.Tk()
    app = VideoDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
