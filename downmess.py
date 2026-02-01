import os
import sys
import threading
import subprocess
import json
import time
from datetime import datetime
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import urllib.request
import io
import io
import webbrowser
import random
# --- Dependency Management ---
def install_dependencies():
    """Check and install missing python dependencies."""
    required = ["customtkinter", "yt-dlp", "Pillow", "plyer", "opencv-python", "rembg", "flet", "tkinterdnd2", "librosa", "numpy", "matplotlib"]
    missing = []
    
    import importlib.util
    if importlib.util.find_spec("customtkinter") is None: missing.append("customtkinter")
    if importlib.util.find_spec("yt_dlp") is None: missing.append("yt-dlp")
    if importlib.util.find_spec("PIL") is None: missing.append("Pillow")
    if importlib.util.find_spec("plyer") is None: missing.append("plyer")
    if importlib.util.find_spec("cv2") is None: missing.append("opencv-python")
    if importlib.util.find_spec("rembg") is None: missing.append("rembg")
    if importlib.util.find_spec("flet") is None: missing.append("flet")
    if importlib.util.find_spec("tkinterdnd2") is None: missing.append("tkinterdnd2")
    if importlib.util.find_spec("librosa") is None: missing.append("librosa")
    if importlib.util.find_spec("numpy") is None: missing.append("numpy")
    if importlib.util.find_spec("matplotlib") is None: missing.append("matplotlib")
    
    if missing:
        print(f"Missing dependencies found: {', '.join(missing)}")
        print("Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("Dependencies installed successfully.")
        except Exception as e:
            print(f"Error installing dependencies: {e}")

try:
    import customtkinter as ctk
    import yt_dlp
    from plyer import notification
    from PIL import Image
except ImportError:
    install_dependencies()
    import customtkinter as ctk
    import yt_dlp
    from plyer import notification
    from PIL import Image

from downmess_core import DownmessCore

# --- UI / Theme Settings ---
# --- UI / Theme Settings ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # Using base theme, but we will override manually

# --- Constants & Config (Messrack Luxury Tech) ---
# PRIMARY PALETTE
DOWNMESS_BG = "#1A1A1A"          # Matte Black (Main background)
DOWNMESS_OBSIDIAN = "#0F0F0F"    # Deep Black (Cards, input fields)
DOWNMESS_GOLD = "#D4AF37"        # Luxury Gold (Accents, active states)
DOWNMESS_TEXT = "#E0E0E0"        # Off-white Text
DOWNMESS_STEEL = "#4A4A4A"       # Inactive elements

# COMPONENT POINTERS (Backwards compatibility with old vars)
DOWNMESS_RED = DOWNMESS_GOLD     # Replaces Red with Gold
DOWNMESS_CYAN = DOWNMESS_GOLD    # Replaces Cyan with Gold
DOWNMESS_GREEN = DOWNMESS_GOLD   # Replaces Green with Gold (Success state)
DOWNMESS_CARD = DOWNMESS_OBSIDIAN
DOWNMESS_ACCENT = "#B5952F"      # Darker Gold for hover

# TYPOGRAPHY
DOWNMESS_FONT_HEADER = ("Montserrat", 40, "bold") # Or Impact if Montserrat unavailable
DOWNMESS_FONT_SUB = ("Montserrat", 12, "bold")    # Spaced caps style
DOWNMESS_FONT_BODY = ("Roboto", 12)


HISTORY_FILE = "downmess_history.json"


# --- INICIO DEL PARCHE PARA EL EXE ---
def fix_dnd_path():
    # Solo se ejecuta si estamos en el modo compilado (.exe)
    if getattr(sys, 'frozen', False):
        # Busca la ruta interna donde PyInstaller descomprime los archivos
        dnd_path = os.path.join(sys._MEIPASS, 'tkinterdnd2')
        # Le dice al sistema dónde está la librería
        os.environ['TKDND_LIBRARY'] = dnd_path
# --- FIN DEL PARCHE ---

# IMPORTANTE: Llama a esta función ANTES de crear la ventana de la app
fix_dnd_path()

class DownmessApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Window Setup
        self.title("DOWNMESS | Descargador Definitivo")
        if os.path.exists("downmess.ico"):
            self.iconbitmap("downmess.ico")
        self.geometry("1000x800")
        self.configure(fg_color=DOWNMESS_BG)
        
        # Clipboard Monitor State
        self.monitor_clipboard = ctk.BooleanVar(value=False)
        self.last_clipboard = ""

        # Core Logic
        self.core = DownmessCore()

        # Start Clipboard Monitor Loop
        self.after(2000, self.check_clipboard)

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Main Content

        # 1. Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        self.logo_image = None
        logo_path = "downmess_logo.png"
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
            except: pass

        if self.logo_image:
            ctk.CTkLabel(self.header_frame, text="", image=self.logo_image).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.header_frame, 
            text="DOWNMESS", 
            font=DOWNMESS_FONT_HEADER, 
            text_color=DOWNMESS_TEXT
        ).pack(side="left", pady=10)

        # 2. Interactive Banner (Canvas Animation)
        self.banner_canvas = ctk.CTkCanvas(self.header_frame, height=40, bg=DOWNMESS_BG, highlightthickness=0)
        self.banner_canvas.pack(side="left", fill="x", expand=True, padx=20)
        self.start_banner_animation()

        # Open Folder Button
        self.open_folder_btn = ctk.CTkButton(
            self.header_frame,
            text="[ ABRIR CARPETA ]",
            font=DOWNMESS_FONT_SUB,
            width=140,
            height=32,
            fg_color="transparent",
            hover_color=DOWNMESS_STEEL,
            border_color=DOWNMESS_GOLD,
            border_width=1,
            corner_radius=0, # Geometric
            text_color=DOWNMESS_GOLD,
            command=self.open_download_folder
        )
        self.open_folder_btn.pack(side="right", pady=10)

        # 2. Main Tab View
        self.tab_view = ctk.CTkTabview(
            self, 
            fg_color=DOWNMESS_CARD,
            segmented_button_fg_color=DOWNMESS_BG,
            segmented_button_selected_color=DOWNMESS_GOLD,
            segmented_button_selected_hover_color=DOWNMESS_ACCENT,
            segmented_button_unselected_color=DOWNMESS_BG,
            segmented_button_unselected_hover_color=DOWNMESS_OBSIDIAN,
            text_color="white" # Keep white for readability on dark tabs
        )
        self.tab_view.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.tab_view._segmented_button.configure(font=("Roboto Medium", 14))
        
        # Tabs
        self.tab_downloader = self.tab_view.add("DESCARGADOR")
        self.tab_converter = self.tab_view.add("CONVERTIDOR")
        self.tab_discovery = self.tab_view.add("BUSCADOR")
        self.tab_history = self.tab_view.add("HISTORIAL")
        self.tab_tools = self.tab_view.add("HERRAMIENTAS IA")
        
        self.setup_downloader_tab()
        self.setup_converter_tab()
        self.setup_discovery_tab()
        self.setup_history_tab()
        self.setup_tools_tab()

    def check_clipboard(self):
        """Monitors clipboard for valid URLs."""
        if self.monitor_clipboard.get():
            try:
                content = self.clipboard_get()
                if content != self.last_clipboard:
                    self.last_clipboard = content
                    if "youtube.com" in content or "youtu.be" in content or "soundcloud.com" in content:
                        # Auto-paste
                        current_text = self.url_textbox.get("1.0", "end-1c")
                        if content not in current_text:
                            # If box is empty, just paste. If not, append new line
                            if not current_text.strip():
                                self.url_textbox.insert("1.0", content)
                            else:
                                self.url_textbox.insert("end", "\n" + content)
                            
                            self.core.send_notification("Downmess", "¡Enlace detectado y pegado!")
            except: pass
        self.after(2000, self.check_clipboard)

    # --- Setup Tabs ---

    def setup_downloader_tab(self):
        self.tab_downloader.grid_columnconfigure(0, weight=1)
        self.tab_downloader.grid_rowconfigure(5, weight=1) # Allow expansion for grid

        # Input Area (Expanded)
        input_frame = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(input_frame, text="Pegar Enlaces (Uno por línea):", text_color=DOWNMESS_CYAN, font=("Roboto Bold", 14)).pack(anchor="w", pady=(0, 5))
        
        self.url_textbox = ctk.CTkTextbox(
            input_frame, 
            font=("Roboto", 14),
            fg_color=DOWNMESS_OBSIDIAN,
            text_color=DOWNMESS_TEXT,
            border_color=DOWNMESS_GOLD,
            border_width=1,
            corner_radius=0,
            height=150
        )
        self.url_textbox.pack(fill="x")
        
        # --- Drag & Drop for URL ---
        self.url_textbox.drop_target_register(DND_FILES)
        self.url_textbox.dnd_bind('<<Drop>>', self.on_drop_url)

        # Options Row
        self.dl_options_frame = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        self.dl_options_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        # Quality
        self.quality_var = ctk.StringVar(value="1080p")
        vals = ["Mejor Calidad (4K/8K)", "1080p", "720p", "Solo Audio (MP3 320kbps)", "Solo Audio (WAV)"]
        self.quality_combo = ctk.CTkComboBox(
            self.dl_options_frame,
            values=vals,
            variable=self.quality_var,
            width=200,
            fg_color=DOWNMESS_OBSIDIAN,
            border_color=DOWNMESS_GOLD,
            button_color=DOWNMESS_GOLD,
            dropdown_fg_color=DOWNMESS_OBSIDIAN,
            dropdown_hover_color=DOWNMESS_STEEL,
            dropdown_text_color=DOWNMESS_TEXT,
            text_color=DOWNMESS_TEXT,
            corner_radius=0
        )
        self.quality_combo.pack(side="left", padx=(0, 10))

        # Switch
        self.clip_switch = ctk.CTkSwitch(
            self.dl_options_frame, 
            text="AUTO-PEGAR",
            font=("Roboto", 10, "bold"),
            variable=self.monitor_clipboard,
            progress_color=DOWNMESS_GOLD,
            button_color=DOWNMESS_TEXT,
            button_hover_color=DOWNMESS_GOLD,
            fg_color=DOWNMESS_STEEL
        )
        self.clip_switch.pack(side="left", padx=10)

        # Normalize Switch
        self.normalize_var = ctk.BooleanVar(value=True)
        self.norm_switch = ctk.CTkSwitch(
            self.dl_options_frame,
            text="NORMALIZAR",
            font=("Roboto", 10, "bold"),
            variable=self.normalize_var,
            progress_color=DOWNMESS_GOLD,
            button_color=DOWNMESS_TEXT,
            button_hover_color=DOWNMESS_GOLD,
            fg_color=DOWNMESS_STEEL
        )
        self.norm_switch.pack(side="left", padx=10)

        # --- Time Range Inputs ---
        time_frame = ctk.CTkFrame(self.dl_options_frame, fg_color="transparent")
        time_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(time_frame, text="Recorte:", font=("Roboto", 10), text_color="gray").pack(side="top")
        range_inner = ctk.CTkFrame(time_frame, fg_color="transparent")
        range_inner.pack()
        
        self.start_time_var = ctk.StringVar(value="")
        self.end_time_var = ctk.StringVar(value="")
        
        self.start_entry = ctk.CTkEntry(range_inner, placeholder_text="00:00", width=60, font=("Roboto", 12), border_color=DOWNMESS_CYAN)
        self.start_entry.pack(side="left", padx=2)
        ctk.CTkLabel(range_inner, text="-", text_color=DOWNMESS_CYAN).pack(side="left")
        self.end_entry = ctk.CTkEntry(range_inner, placeholder_text="Fin", width=60, font=("Roboto", 12), border_color=DOWNMESS_CYAN)
        self.end_entry.pack(side="left", padx=2)

        # Buttons
        self.download_btn = ctk.CTkButton(
            self.dl_options_frame,
            text="EJECUTAR DESCARGA",
            font=DOWNMESS_FONT_SUB,
            fg_color=DOWNMESS_GOLD,
            text_color="black", # Contrast on gold
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            height=32,
            command=self.start_batch_download_thread
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=10)

        self.reset_btn = ctk.CTkButton(
            self.dl_options_frame,
            text="RESET",
            font=DOWNMESS_FONT_SUB,
            fg_color="transparent",
            border_color=DOWNMESS_STEEL,
            border_width=1,
            hover_color=DOWNMESS_STEEL,
            text_color="gray",
            width=80,
            height=32,
            corner_radius=0,
            command=self.reset_downloader_ui
        )
        self.reset_btn.pack(side="left")

        # Progress & Status
        status_frame = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        status_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.status_label = ctk.CTkLabel(status_frame, text="Esperando...", text_color="gray70", anchor="w")
        self.status_label.pack(fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(
            status_frame, 
            progress_color=DOWNMESS_GOLD,
            fg_color=DOWNMESS_STEEL,
            height=6,
            corner_radius=0
        )
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)

        # --- Supported Platforms Grid ---
        ctk.CTkLabel(self.tab_downloader, text="PLATAFORMAS COMPATIBLES", text_color=DOWNMESS_GOLD, font=("Montserrat", 16, "bold")).grid(row=3, column=0, pady=(30, 10))
        
        self.platforms_frame = ctk.CTkScrollableFrame(self.tab_downloader, fg_color="transparent", height=200)
        self.platforms_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        platforms = [
            ("YouTube", "#FF0000", "https://www.youtube.com"), 
            ("SoundCloud", "#FF5500", "https://soundcloud.com"), 
            ("TikTok", "#00F2EA", "https://www.tiktok.com"), 
            ("Spotify", "#1DB954", "https://open.spotify.com"), 
            ("Twitch", "#9146FF", "https://www.twitch.tv"), 
            ("Twitter/X", "#ffffff", "https://twitter.com"),
            ("Instagram", "#E1306C", "https://www.instagram.com"), 
            ("Facebook", "#1877F2", "https://www.facebook.com"), 
            ("Vimeo", "#1AB7EA", "https://vimeo.com"),
            ("DailyMotion", "#0066DC", "https://www.dailymotion.com"), 
            ("Bandcamp", "#629AA9", "https://bandcamp.com"), 
            ("Mixcloud", "#5000ff", "https://www.mixcloud.com")
        ]
        
        # Grid layout for platforms
        cols = 4
        for i, (name, color, url) in enumerate(platforms):
            r = i // cols
            c = i % cols
            self.create_platform_card(self.platforms_frame, name, color, url, r, c)

    def create_platform_card(self, parent, name, color, url, r, c):
        # Flattened, bordered card
        card = ctk.CTkFrame(parent, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_STEEL, border_width=1, corner_radius=0)
        card.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
        parent.grid_columnconfigure(c, weight=1)
        
        # Click event
        card.bind("<Button-1>", lambda e: webbrowser.open(url))
        card.bind("<Enter>", lambda e: card.configure(fg_color="#222", border_color=color))
        card.bind("<Leave>", lambda e: card.configure(fg_color=DOWNMESS_CARD, border_color=DOWNMESS_CYAN))
        
        # Color strip
        strip = ctk.CTkFrame(card, fg_color=color, height=5, corner_radius=0)
        strip.pack(fill="x")
        strip.bind("<Button-1>", lambda e: webbrowser.open(url))
        
        lbl = ctk.CTkLabel(card, text=name, font=("Roboto Bold", 12), text_color="white")
        lbl.pack(pady=10)
        lbl.bind("<Button-1>", lambda e: webbrowser.open(url))

    # --- Converter Tab Redesign ---
    def setup_converter_tab(self):
        self.tab_converter.grid_columnconfigure(0, weight=1)
        self.tab_converter.grid_columnconfigure(1, weight=1)
        self.tab_converter.grid_rowconfigure(1, weight=1)
        
        # Left Panel: Controls
        controls_frame = ctk.CTkFrame(self.tab_converter, fg_color="transparent")
        controls_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        self.file_select_btn = ctk.CTkButton(
            controls_frame, 
            text="+ AÑADIR ARCHIVOS", 
            font=DOWNMESS_FONT_SUB, 
            height=40,
            fg_color=DOWNMESS_OBSIDIAN, 
            border_color=DOWNMESS_GOLD, 
            border_width=1, 
            corner_radius=0,
            text_color=DOWNMESS_GOLD,
            hover_color=DOWNMESS_STEEL,
            command=self.select_files
        )
        self.file_select_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # DnD for Button
        self.file_select_btn.drop_target_register(DND_FILES)
        self.file_select_btn.dnd_bind('<<Drop>>', self.on_drop_files)
        
        self.convert_btn = ctk.CTkButton(
            controls_frame, 
            text="INICIAR CONVERSIÓN", 
            font=DOWNMESS_FONT_SUB,
            height=40,
            fg_color=DOWNMESS_GOLD, 
            text_color="black",
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            command=self.start_conversion_thread
        )
        self.convert_btn.pack(side="right", fill="x", expand=True)

        # Options
        options_frame = ctk.CTkFrame(self.tab_converter, fg_color="transparent")
        options_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        
        ctk.CTkLabel(options_frame, text="Formato:", font=DOWNMESS_FONT_BODY).pack(side="left")
        self.format_var = ctk.StringVar(value="MP3")
        formats = ["MP4", "MKV", "MOV", "MP3", "WAV", "FLAC", "OGG", "M4A", "JPG", "PNG", "WEBP", "GIF"]
        ctk.CTkComboBox(options_frame, values=formats, variable=self.format_var, width=100, font=DOWNMESS_FONT_BODY).pack(side="left", padx=10)
        
        self.norm_conv_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(options_frame, text="Normalizar Audio", variable=self.norm_conv_var, font=DOWNMESS_FONT_BODY, progress_color=DOWNMESS_CYAN).pack(side="left", padx=20)

        # Main Area: Split View
        # Left: Queue List
        self.queue_frame = ctk.CTkScrollableFrame(self.tab_converter, label_text="Cola de Archivos", label_font=DOWNMESS_FONT_SUB, fg_color=DOWNMESS_CARD)
        self.queue_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        
        # Right: Dropped Zone / Details (Empty Space Filler)
        self.details_frame = ctk.CTkFrame(self.tab_converter, fg_color=DOWNMESS_CARD, border_color="#333", border_width=1)
        self.details_frame.grid(row=2, column=1, padx=20, pady=20, sticky="nsew")
        
        # Drop Zone Visual
        self.details_label = ctk.CTkLabel(
            self.details_frame, 
            text="ARRASTRA ARCHIVOS AQUÍ\n\n[ ZONA DE CARGA ]", 
            font=DOWNMESS_FONT_HEADER, 
            text_color="#333"
        )
        self.details_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.details_frame.drop_target_register(DND_FILES)
        self.details_frame.dnd_bind('<<Drop>>', self.on_drop_files)
        
        self.file_list = []
        self.queue_widgets = []
        
        self.conv_status = ctk.CTkLabel(self.tab_converter, text="", text_color=DOWNMESS_CYAN, font=DOWNMESS_FONT_BODY)
        self.conv_status.grid(row=3, column=0, columnspan=2, pady=10)

    def update_queue_ui(self):
        for w in self.queue_widgets: w.destroy()
        self.queue_widgets = []
        
        for f in self.file_list:
            card = ctk.CTkFrame(self.queue_frame, fg_color="transparent", border_color="#333", border_width=1)
            card.pack(fill="x", pady=2)
            
            name = os.path.basename(f)
            ctk.CTkLabel(card, text=name, font=("Consolas", 11), anchor="w").pack(side="left", padx=5)
            ctk.CTkButton(card, text="X", width=30, fg_color="#333", hover_color=DOWNMESS_RED, command=lambda p=f: self.remove_from_queue(p)).pack(side="right")
            
            self.queue_widgets.append(card)
            
    def remove_from_queue(self, path):
        if path in self.file_list:
            self.file_list.remove(path)
            self.update_queue_ui()

    def select_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.file_list.extend(files)
            self.update_queue_ui()
            
    # Modified Handler to update UI
    def on_drop_files(self, event):
        """Handle dropped files for conversion"""
        data = event.data
        if data:
            import shlex, re
            try:
                data = data.replace("\\", "/")
                if "{" in data:
                    pattern = r'\{(?P<quoted>.*?)\}|(?P<plain>[^ ]+)'
                    matches = re.finditer(pattern, data)
                    files = []
                    for m in matches:
                        if m.group('quoted'): files.append(m.group('quoted'))
                        elif m.group('plain'): files.append(m.group('plain'))
                else: # Fallback for no spaces/quotes
                    files = data.split()
                
                valid_files = [f for f in files if os.path.isfile(f)]
                self.file_list.extend(valid_files)
                self.update_queue_ui()
                self.core.send_notification("Downmess", f"{len(valid_files)} archivos añadidos")
            except Exception as e:
                print(f"DnD Error: {e}") 

    def start_conversion_thread(self): # Keep same logic but update UI status
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        fmt = self.format_var.get().lower()
        normalize = self.norm_conv_var.get()
        self.convert_btn.configure(state="disabled", text="CONVIRTIENDO...")
        
        total = len(self.file_list)
        for i, fp in enumerate(self.file_list):
            try:
                self.conv_status.configure(text=f"Convirtiendo {i+1}/{total}: {os.path.basename(fp)}")
                self.core.convert_file(fp, fmt, normalize=normalize)
            except: pass
        
        self.conv_status.configure(text="¡Conversión Terminada!", text_color=DOWNMESS_GREEN)
        self.convert_btn.configure(state="normal", text="INICIAR CONVERSIÓN")
        self.file_list = []
        self.update_queue_ui()
        self.core.send_notification('Downmess', '¡Conversión Completa!')

    def setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(1, weight=1)
        
        # Header / Controls
        ctrl_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        ctrl_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(
            ctrl_frame, 
            text="ACTUALIZAR", 
            font=DOWNMESS_FONT_SUB,
            fg_color="#222", 
            width=120,
            command=self.refresh_history_ui
        ).pack(side="left")
        
        ctk.CTkLabel(ctrl_frame, text="HISTORIAL DE DESCARGAS", font=DOWNMESS_FONT_SUB, text_color=DOWNMESS_CYAN).pack(side="right")

        # History List
        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
        self.history_scroll.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.refresh_history_ui()

    def refresh_history_ui(self):
        # Clear existing
        for w in self.history_scroll.winfo_children():
            w.destroy()
            
        history_data = self.core.history
        
        if not history_data:
            ctk.CTkLabel(self.history_scroll, text="No hay historial reciente.", text_color="gray").pack(pady=20)
            return

        for item in history_data:
            card = ctk.CTkFrame(self.history_scroll, fg_color=DOWNMESS_CARD, border_color="#333", border_width=1)
            card.pack(fill="x", pady=5)
            
            # Info
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            
            ctk.CTkLabel(info, text=item['title'], font=("Consolas", 12, "bold"), text_color="white", anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"{item['date']} | {item['quality']}", font=("Consolas", 10), text_color="gray", anchor="w").pack(fill="x")
            
            # Actions
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(
                btn_frame, 
                text="COPIAR LINK", 
                width=80, 
                font=("Consolas", 10),
                fg_color="#333", 
                hover_color=DOWNMESS_CYAN,
                command=lambda u=item['url']: self.copy_to_clipboard(u)
            ).pack(side="right")
            
    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.core.send_notification("Downmess", "Enlace copiado al portapapeles")

    # --- Discovery Tab ---
    def setup_discovery_tab(self):
        self.tab_discovery.grid_columnconfigure(0, weight=1)
        self.tab_discovery.grid_rowconfigure(2, weight=1) # Increase row index for results

        # Search Bar Frame
        search_frame = ctk.CTkFrame(self.tab_discovery, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # Engine Selector
        self.engine_var = ctk.StringVar(value="YouTube")
        self.engine_combo = ctk.CTkComboBox(
            search_frame,
            values=["YouTube", "SoundCloud", "TikTok", "Spotify", "Twitch", "Instagram", "Facebook", "Twitter/X"],
            variable=self.engine_var,
            width=140,
            fg_color=DOWNMESS_OBSIDIAN,
            border_color=DOWNMESS_GOLD,
            button_color=DOWNMESS_GOLD,
            dropdown_fg_color=DOWNMESS_OBSIDIAN,
            corner_radius=0
        )
        self.engine_combo.pack(side="left", padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Buscar música...",
            font=DOWNMESS_FONT_BODY,
            height=32,
            border_color=DOWNMESS_GOLD,
            fg_color=DOWNMESS_OBSIDIAN,
            corner_radius=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.start_search_thread())

        search_btn = ctk.CTkButton(
            search_frame, 
            text="BUSCAR", 
            width=100, 
            height=32,
            font=DOWNMESS_FONT_SUB,
            fg_color=DOWNMESS_GOLD, 
            text_color="black",
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            command=self.start_search_thread
        )
        search_btn.pack(side="right")
        
        # History Frame container (Label + Scroll + Delete)
        hist_container = ctk.CTkFrame(self.tab_discovery, fg_color="transparent")
        hist_container.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Label
        ctk.CTkLabel(hist_container, text="BÚSQUEDAS RECIENTES:", font=("Consolas", 10), text_color="gray").pack(side="left")

        # Scrollable Frame
        self.history_frame = ctk.CTkScrollableFrame(hist_container, height=35, orientation="horizontal", fg_color="transparent")
        self.history_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        # Clear Button
        ctk.CTkButton(
            hist_container,
            text="[BORRAR]",
            width=60,
            font=("Consolas", 10),
            fg_color="#222",
            hover_color=DOWNMESS_RED,
            command=self.clear_search_history
        ).pack(side="right")

        # Results Area
        self.results_scroll = ctk.CTkScrollableFrame(
            self.tab_discovery,
            fg_color="transparent",
            label_text="RESULTADOS ENCONTRADOS",
            label_font=DOWNMESS_FONT_SUB,
            label_text_color=DOWNMESS_GOLD
        )
        self.results_scroll.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.populate_search_history()

    def populate_search_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        for term in self.core.search_history:
            btn = ctk.CTkButton(
                self.history_frame, 
                text=term, 
                font=("Roboto", 12),
                fg_color="#222", 
                hover_color="#333",
                height=30,
                width=20,
                command=lambda t=term: self.search_from_history(t)
            )
            btn.pack(side="left", padx=5)

    def search_from_history(self, term):
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, term)
        self.start_search_thread()

    def clear_search_history(self):
        self.core.clear_search_history()
        self.populate_search_history()
        self.core.send_notification("Downmess", "Historial de búsqueda borrado")

    def start_search_thread(self):
        query = self.search_entry.get()
        if not query: return
        
        # Save History
        self.core.add_search_history(query)
        self.populate_search_history()
        
        engine = self.engine_var.get()
        
        # WEB SEARCH FALLBACK (For non-native engines)
        if engine not in ["YouTube", "SoundCloud"]:
            base_urls = {
                "TikTok": f"https://www.tiktok.com/search?q={query}",
                "Spotify": f"https://open.spotify.com/search/{query}",
                "Twitch": f"https://www.twitch.tv/search?term={query}",
                "Instagram": f"https://www.instagram.com/", 
                "Facebook": f"https://www.facebook.com/search/top?q={query}",
                "Twitter/X": f"https://twitter.com/search?q={query}&src=typed_query"
            }
            
            url = base_urls.get(engine)
            if url:
                webbrowser.open(url)
                self.core.send_notification("Downmess", f"Buscando '{query}' en {engine} (Navegador)...")
                return

        # NATIVE SEARCH (YouTube/SoundCloud)
        engine_map = {"YouTube": "ytsearch", "SoundCloud": "scsearch"}
        engine_code = engine_map.get(engine, "ytsearch")

        # Clear previous
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
            
        loading = ctk.CTkLabel(self.results_scroll, text=f"Buscando en {engine}...", text_color="white")
        loading.pack(pady=20)
        
        threading.Thread(target=self.run_search, args=(query, engine_code, loading), daemon=True).start()

    def run_search(self, query, engine, loading_label):
        results = self.core.search_videos(query, limit=10, engine=engine)
        loading_label.destroy()
        
        if not results:
             ctk.CTkLabel(self.results_scroll, text="No se encontraron resultados.", text_color="gray").pack(pady=20)
             return

        for vid in results:
            # We don't download thumbnails here to keep UI fast, 
            # we'll use a thread/callback for each card.
            self.create_video_card(vid)

    def create_video_card(self, vid_data):
        # Geometric card
        card = ctk.CTkFrame(self.results_scroll, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_STEEL, border_width=1, corner_radius=0)
        card.pack(fill="x", pady=5, padx=5)
        
        # Micro-animation on hover
        card.bind("<Enter>", lambda e: card.configure(border_color=DOWNMESS_GOLD))
        card.bind("<Leave>", lambda e: card.configure(border_color=DOWNMESS_STEEL))
        
        # Thumbnail Frame
        thumb_frame = ctk.CTkFrame(card, width=120, height=68, fg_color=DOWNMESS_BG)
        thumb_frame.pack(side="left", padx=10, pady=10)
        thumb_frame.pack_propagate(False)
        
        thumb_label = ctk.CTkLabel(thumb_frame, text="...", text_color="gray")
        thumb_label.pack(expand=True)
        
        # Fetch thumbnail in background
        if vid_data.get('thumbnail'):
            threading.Thread(target=self.load_thumbnail, args=(vid_data['thumbnail'], thumb_label), daemon=True).start()
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        title_lbl = ctk.CTkLabel(
            info_frame, 
            text=vid_data['title'], 
            font=("Roboto Bold", 14), 
            text_color="white", 
            anchor="w",
            wraplength=600
        )
        title_lbl.pack(fill="x")
        
        meta_text = f"Duración: {self.format_seconds(vid_data['duration'])} | {vid_data['uploader']}"
        meta_lbl = ctk.CTkLabel(info_frame, text=meta_text, font=("Roboto", 11), text_color="gray", anchor="w")
        meta_lbl.pack(fill="x")

        # Actions
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=10)

        # "Preview" -> Open in Browser
        preview_btn = ctk.CTkButton(
            action_frame, 
            text="VER",
            width=50,
            height=28,
            font=("Roboto Bold", 10),
            fg_color="transparent",
            border_color=DOWNMESS_STEEL,
            border_width=1,
            hover_color=DOWNMESS_STEEL,
            corner_radius=0,
            command=lambda u=vid_data['url']: webbrowser.open(u)
        )
        preview_btn.pack(side="left", padx=5)

        # "Download" -> Send to Tab
        dl_btn = ctk.CTkButton(
            action_frame, 
            text="SELECCIONAR",
            width=120,
            height=28,
            font=("Roboto Bold", 10),
            fg_color=DOWNMESS_GOLD,
            text_color="black",
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            command=lambda u=vid_data['url']: self.select_video_for_download(u)
        )
        dl_btn.pack(side="left")

    def select_video_for_download(self, url):
        self.tab_view.set("DESCARGADOR")
        self.url_textbox.insert("end", url + "\n")
        self.core.send_notification("Downmess", "Video añadido a la cola de descarga")

    def format_seconds(self, seconds):
        if not seconds: return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h: return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    # --- Logic ---

    def start_batch_download_thread(self):
        raw_text = self.url_textbox.get("1.0", "end-1c")
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not urls: return

        self.download_btn.configure(state="disabled")
        self.progress_bar.configure(progress_color=DOWNMESS_RED, mode="indeterminate")
        self.progress_bar.start()
        self.status_label.configure(text="Iniciando...", text_color="white")
        
        threading.Thread(target=self.run_batch_download, args=(urls,), daemon=True).start()

    def run_batch_download(self, urls):
        quality = self.quality_var.get()
        normalize = self.normalize_var.get()
        s_time = self.start_entry.get().strip()
        e_time = self.end_entry.get().strip()
        
        # Stop animation
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")

        total = len(urls)
        
        try:
            for i, url in enumerate(urls):
                self.progress_bar.set(0)
                self.status_label.configure(text=f"Descargando {i+1}/{total}: {url}")
                
                # Delegate to Core
                self.core.download_url(url, quality, normalize=normalize, 
                                     progress_hook=self.progress_hook,
                                     start_time=s_time if s_time else None,
                                     end_time=e_time if e_time else None)
            
            # Success State
            self.progress_bar.set(1.0)
            self.progress_bar.configure(progress_color=DOWNMESS_CYAN)
            self.status_label.configure(text="TODAS LAS TAREAS COMPLETADAS CON ÉXITO", text_color=DOWNMESS_CYAN)
            
            self.core.send_notification('Downmess', '¡Descarga por lotes finalizada con éxito!')

        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color=DOWNMESS_RED)
        finally:
            self.download_btn.configure(state="normal")
            self.refresh_history_ui()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Calculate progress from bytes (more reliable than _percent_str)
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total:
                    p = downloaded / total
                    self.progress_bar.set(p)
                    
                    # Update text with percentage for better feedback
                    percent_text = f"{p*100:.1f}%"
                    current_text = self.status_label.cget("text").split(":")[0] # Keep "Descargando X/Y"
                    if "Descargando" in current_text:
                        self.status_label.configure(text=f"{current_text}: {percent_text}")
                else:
                    # Fallback
                    p = d.get('_percent_str', '0%').replace('%','')
                    self.progress_bar.set(float(p)/100)
            except: pass

    def reset_downloader_ui(self):
        """Resets the downloader tab validation and progress."""
        self.url_textbox.delete("1.0", "end")
        self.start_entry.delete(0, "end")
        self.end_entry.delete(0, "end")
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=DOWNMESS_RED, mode="determinate")
        self.status_label.configure(text="Esperando...", text_color="gray70")
        self.download_btn.configure(state="normal")

    def load_thumbnail(self, url, label):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            pil_img = Image.open(io.BytesIO(raw_data))
            # Resize for the card
            pil_img = pil_img.resize((120, 68), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 68))
            label.configure(image=ctk_img, text="")
            label.image = ctk_img # Keep ref
        except:
            label.configure(text="Error")

    # --- History Logic ---    
    # Logic is now in setup_history_tab (above)

    # --- Player Logic ---


    # --- Utils ---
    def open_download_folder(self):
        os.startfile(os.getcwd())

    # --- Drag & Drop Handlers ---
    def on_drop_url(self, event):
        """Handle dropped URLs or text file containing URLs"""
        data = event.data
        if data:
            # Clean curly braces often added by TkinterDnD for paths with spaces
            data = data.replace("{", "").replace("}", "")
            self.url_textbox.insert("end", data + "\n")
            self.core.send_notification("Downmess", "Enlace añadido por arrastre")

    def on_drop_files(self, event):
        """Handle dropped files for conversion"""
        data = event.data
        if data:
            # Handle multiple files (TkinterDnD returns space separated paths in curly braces if spaces exist)
            # This is a basic parser, might need more robust splitting for complex paths
            # For now, we assume standard behavior
            import shlex
            try:
                # Normalize slashes
                data = data.replace("\\", "/")
                # If possibly multiple files
                if "{" in data:
                    # Regex split or simple replace logic
                    # A robust way is to use regex to find {path with spaces} or path_without_spaces
                    import re
                    pattern = r'\{(?P<quoted>.*?)\}|(?P<plain>[^ ]+)'
                    matches = re.finditer(pattern, data)
                    files = []
                    for m in matches:
                        if m.group('quoted'): files.append(m.group('quoted'))
                        elif m.group('plain'): files.append(m.group('plain'))
                else:
                    files = data.split()
                
                self.file_list.extend(files)
                self.files_label.configure(text=f"{len(self.file_list)} archivos en cola (Añadidos por Drag & Drop)")
                self.core.send_notification("Downmess", f"{len(files)} archivos añadidos")
            except Exception as e:
                print(f"DnD Error: {e}")

    # --- Converter Logic (Concise) ---
    def select_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.file_list = files
            self.files_label.configure(text=f"{len(files)} archivos en cola")

    def start_conversion_thread(self):
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        fmt = self.format_var.get().lower()
        normalize = self.norm_conv_var.get()
        self.convert_btn.configure(state="disabled")
        
        for fp in self.file_list:
            try:
                self.core.convert_file(fp, fmt, normalize=normalize)
            except: pass
        
        self.conv_status.configure(text="¡Conversión Terminada!", text_color=DOWNMESS_GREEN)
        self.convert_btn.configure(state="normal")
        self.file_list = []
        self.core.send_notification('Downmess', '¡Conversión Completa!')

    # --- AI Tools Tab ---
    # --- AI Tools Tab ---
    def setup_tools_tab(self):
        self.tab_tools.grid_columnconfigure(0, weight=1)
        self.tab_tools.grid_columnconfigure(1, weight=1)
        self.tab_tools.grid_columnconfigure(2, weight=1)
        
        # --- Left: Audio Analyzer (New) ---
        analyzer_frame = ctk.CTkFrame(self.tab_tools, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_GOLD, border_width=1, corner_radius=0)
        analyzer_frame.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")
        
        ctk.CTkLabel(analyzer_frame, text="ANALIZADOR DE AUDIO", font=("Montserrat", 20, "bold"), text_color=DOWNMESS_GOLD).pack(pady=10)
        
        self.analyze_btn = ctk.CTkButton(
            analyzer_frame, 
            text="SELECCIONAR AUDIO", 
            font=DOWNMESS_FONT_SUB,
            fg_color=DOWNMESS_GOLD, 
            text_color="black",
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            command=self.select_audio_for_analysis
        )
        self.analyze_btn.pack(pady=10)
        
        # Details
        self.analysis_results_frame = ctk.CTkFrame(analyzer_frame, fg_color="transparent")
        self.analysis_results_frame.pack(fill="both", expand=True, padx=10)
        
        self.bpm_label = ctk.CTkLabel(self.analysis_results_frame, text="BPM: --", font=("Consolas", 24), text_color=DOWNMESS_GOLD)
        self.bpm_label.pack(pady=5)
        
        self.key_label = ctk.CTkLabel(self.analysis_results_frame, text="KEY: --", font=("Consolas", 24), text_color=DOWNMESS_GOLD)
        self.key_label.pack(pady=5)
        
        self.wave_label = ctk.CTkLabel(self.analysis_results_frame, text="", height=100)
        self.wave_label.pack(pady=10, fill="x")

        # --- Right: Image Tools (Resizing/Upscale) ---
        img_frame = ctk.CTkFrame(self.tab_tools, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_GOLD, border_width=1, corner_radius=0)
        img_frame.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")
        
        ctk.CTkLabel(img_frame, text="UTILIDADES DE IMAGEN", font=("Montserrat", 20, "bold"), text_color=DOWNMESS_GOLD).pack(pady=10)
        
        self.resize_file_var = ctk.StringVar(value="Arrastra o selecciona imagen")
        ctk.CTkButton(
            img_frame, 
            text="SELECCIONAR IMAGEN", 
            font=DOWNMESS_FONT_SUB, 
            command=lambda: self.select_single_file(self.resize_file_var), 
            fg_color=DOWNMESS_STEEL,
            hover_color="#555",
            corner_radius=0
        ).pack(pady=10)
        
        # Presets
        self.preset_var = ctk.StringVar(value="Full HD (1920x1080)")
        presets = ["Full HD (1920x1080)", "4K (3840x2160)", "Insta Post (1080x1080)", "Insta Story (1080x1920)"]
        ctk.CTkComboBox(
            img_frame, 
            values=presets, 
            variable=self.preset_var, 
            width=200, 
            font=DOWNMESS_FONT_BODY,
            fg_color=DOWNMESS_OBSIDIAN,
            border_color=DOWNMESS_GOLD,
            corner_radius=0
        ).pack(pady=10)
        
        ctk.CTkButton(
            img_frame, 
            text="APLICAR CAMBIOS", 
            font=DOWNMESS_FONT_SUB, 
            fg_color=DOWNMESS_GOLD, 
            text_color="black", 
            hover_color=DOWNMESS_ACCENT,
            corner_radius=0,
            command=self.apply_preset
        ).pack(pady=20)
        
        # DnD
        img_frame.drop_target_register(DND_FILES)
        img_frame.dnd_bind('<<Drop>>', self.drop_resize)

        # --- Section 2 (Restored): Manual Resizing ---
        dim_frame = ctk.CTkFrame(img_frame, fg_color="transparent")
        dim_frame.pack(pady=5)
        
        self.resize_w = ctk.CTkEntry(
            dim_frame, 
            placeholder_text="Ancho", 
            width=70,
            fg_color=DOWNMESS_OBSIDIAN,
            border_color=DOWNMESS_GOLD,
            corner_radius=0
        )
        self.resize_w.pack(side="left", padx=5)
        self.resize_h = ctk.CTkEntry(
            dim_frame, 
            placeholder_text="Alto", 
            width=70,
            fg_color=DOWNMESS_OBSIDIAN,
            border_color=DOWNMESS_GOLD,
            corner_radius=0
        )
        self.resize_h.pack(side="left", padx=5)
        
        ctk.CTkButton(
            img_frame, 
            text="ESCALAR", 
            fg_color=DOWNMESS_GOLD, 
            text_color="black",
            hover_color=DOWNMESS_ACCENT, 
            corner_radius=0,
            command=self.start_resize_thread
        ).pack(pady=20)
        
        # --- Section 3: AI Upscaling ---
        upscale_frame = ctk.CTkFrame(self.tab_tools, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_GOLD, border_width=1, corner_radius=0)
        upscale_frame.grid(row=0, column=2, padx=10, pady=20, sticky="nsew") # Moved to col 2
        
        # DnD
        upscale_frame.drop_target_register(DND_FILES)
        upscale_frame.dnd_bind('<<Drop>>', self.drop_upscale)
        
        ctk.CTkLabel(upscale_frame, text="MEJORA IA", text_color=DOWNMESS_GOLD, font=("Montserrat", 20, "bold")).pack(pady=10)
        
        self.upscale_file_var = ctk.StringVar(value="Arrastra aquí o selecciona")
        ctk.CTkButton(upscale_frame, text="SELECCIONAR IMAGEN", font=DOWNMESS_FONT_SUB, command=lambda: self.select_single_file(self.upscale_file_var), fg_color="#333", hover_color="#444").pack(pady=5)
        ctk.CTkLabel(upscale_frame, textvariable=self.upscale_file_var, font=("Consolas", 10), wraplength=150).pack()
        
        opts_frame = ctk.CTkFrame(upscale_frame, fg_color="transparent")
        opts_frame.pack(pady=10)
        
        self.ai_model_var = ctk.StringVar(value="edsr")
        ctk.CTkComboBox(opts_frame, values=["edsr", "espcn", "fsrcnn"], variable=self.ai_model_var, width=90).pack(side="left", padx=5)
        
        self.ai_scale_var = ctk.StringVar(value="4")
        ctk.CTkComboBox(opts_frame, values=["2", "3", "4"], variable=self.ai_scale_var, width=60).pack(side="left", padx=5)
        
        ctk.CTkButton(upscale_frame, text="MEJORAR", font=DOWNMESS_FONT_SUB, fg_color=DOWNMESS_RED, hover_color=DOWNMESS_ACCENT, command=self.start_upscale_thread).pack(pady=20)

        # --- Section 4: Remove Background ---
        bg_frame = ctk.CTkFrame(self.tab_tools, fg_color=DOWNMESS_OBSIDIAN, border_color=DOWNMESS_GOLD, border_width=1, corner_radius=0)
        bg_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=20, sticky="nsew")

        # DnD
        bg_frame.drop_target_register(DND_FILES)
        bg_frame.dnd_bind('<<Drop>>', self.drop_bg)

        ctk.CTkLabel(bg_frame, text="ELIMINAR FONDO", text_color=DOWNMESS_GOLD, font=("Montserrat", 20, "bold")).pack(pady=10)

        self.bg_file_var = ctk.StringVar(value="Arrastra aquí o selecciona")
        ctk.CTkButton(bg_frame, text="SELECCIONAR IMAGEN", font=DOWNMESS_FONT_SUB, command=lambda: self.select_single_file(self.bg_file_var), fg_color="#333", hover_color="#444").pack(pady=5)
        ctk.CTkLabel(bg_frame, textvariable=self.bg_file_var, font=("Consolas", 10), wraplength=150).pack()

        ctk.CTkButton(
            bg_frame, 
            text="QUITAR FONDO", 
            font=DOWNMESS_FONT_SUB, 
            fg_color=DOWNMESS_GOLD, 
            text_color="black",
            hover_color=DOWNMESS_ACCENT, 
            corner_radius=0,
            command=self.start_bg_remove_thread
        ).pack(pady=20)
        
        # Status & Path Feedback
        self.ai_status = ctk.CTkEntry(bg_frame, placeholder_text="Resultados aquí...", fg_color="#222", border_color="gray", width=400)
        self.ai_status.pack(pady=10)
        
        ctk.CTkButton(bg_frame, text="ABRIR RESULTADO", width=100, hover_color=DOWNMESS_ACCENT, command=self.open_result_folder).pack(pady=5)

    def select_audio_for_analysis(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.flac *.m4a")])
        if path:
            self.run_analysis(path)

    def run_analysis(self, path):
        self.analyze_btn.configure(state="disabled", text="ANALIZANDO...")
        threading.Thread(target=self._analysis_thread, args=(path,), daemon=True).start()

    def _analysis_thread(self, path):
        try:
            data = self.core.analyze_audio(path)
            self.after(0, lambda: self.show_analysis_results(data))
        except Exception as e:
            print(e)
            self.core.send_notification("Error", str(e))
        finally:
            self.after(0, lambda: self.analyze_btn.configure(state="normal", text="SELECCIONAR AUDIO"))

    def show_analysis_results(self, data):
        self.bpm_label.configure(text=f"BPM: {data['bpm']}")
        self.key_label.configure(text=f"KEY: {data['key']}")
        
        # Load waveform image
        try:
            pil_img = Image.open(io.BytesIO(data['waveform']))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 100))
            self.wave_label.configure(image=ctk_img)
        except: pass

    # --- Missing Helper Methods ---
    def select_single_file(self, string_var):
        path = filedialog.askopenfilename()
        if path:
            string_var.set(path)
            
    def drop_resize(self, event):
        data = event.data
        if data:
            data = data.replace("{", "").replace("}", "")
            self.resize_file_var.set(data)
            
    def drop_upscale(self, event):
        data = event.data
        if data:
            data = data.replace("{", "").replace("}", "")
            self.upscale_file_var.set(data)
            
    def apply_preset(self):
        val = self.preset_var.get()
        mapping = {
            "Full HD (1920x1080)": (1920, 1080),
            "4K (3840x2160)": (3840, 2160),
            "Insta Post (1080x1080)": (1080, 1080),
            "Insta Story (1080x1920)": (1080, 1920)
        }
        res = mapping.get(val)
        if res:
            self.resize_w.delete(0, "end")
            self.resize_w.insert(0, str(res[0]))
            self.resize_h.delete(0, "end")
            self.resize_h.insert(0, str(res[1]))

    def start_resize_thread(self):
        f = self.resize_file_var.get()
        if not os.path.exists(f): return
        threading.Thread(target=self.run_resize, daemon=True).start()

    def run_resize(self):
        f = self.resize_file_var.get()
        w = self.resize_w.get()
        h = self.resize_h.get()
        
        try:
            self.core.resize_image(f, w, h)
            self.core.send_notification("Downmess", "Imagen redimensionada con éxito")
        except Exception as e:
            print(e)
            
    def start_upscale_thread(self):
        f = self.upscale_file_var.get()
        if not os.path.exists(f): return
        threading.Thread(target=self.run_upscale, daemon=True).start()
        
    def run_upscale(self):
        f = self.upscale_file_var.get()
        m = self.ai_model_var.get()
        s = int(self.ai_scale_var.get())
        
        try:
            self.core.send_notification("Downmess", "Mejorando imagen con IA (esto puede tardar)...")
            self.core.upscale_image_ai(f, m, s)
            self.core.send_notification("Downmess", "Imagen mejorada con éxito")
        except Exception as e:
            print(e)
            self.core.send_notification("Error", f"Fallo en IA: {e}")

    def start_banner_animation(self):
        """Matrix rain / Digital bars effect"""
        self.banner_particles = []
        width = 600
        for _ in range(20):
            self.banner_particles.append({
                "x": random.randint(0, width),
                "y": random.randint(0, 40),
                "speed": random.randint(2, 5),
                "char": random.choice(["0", "1"])
            })
        self.animate_banner()

    def animate_banner(self):
        try:
            self.banner_canvas.delete("all")
            width = self.banner_canvas.winfo_width()
            
            for p in self.banner_particles:
                self.banner_canvas.create_text(p["x"], p["y"], text=p["char"], fill=DOWNMESS_CYAN, font=("Consolas", 10))
                p["y"] += p["speed"]
                if p["y"] > 40:
                    p["y"] = 0
                    p["x"] = random.randint(0, width)
            
            self.after(50, self.animate_banner)
        except: pass

    def apply_preset(self, choice):
        if choice == "Personalizado": return
        try:
            # Extract numbers from string like "Full HD (1920x1080)"
            res = choice.split("(")[-1].replace(")", "")
            w, h = res.split("x")
            self.resize_w.delete(0, "end")
            self.resize_w.insert(0, w)
            self.resize_h.delete(0, "end")
            self.resize_h.insert(0, h)
        except: pass

    # DnD Handlers
    def clean_drop_path(self, event):
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        return path

    def drop_resize(self, event):
        p = self.clean_drop_path(event)
        self.resize_file_var.set(p)

    def drop_upscale(self, event):
        p = self.clean_drop_path(event)
        self.upscale_file_var.set(p)

    def drop_bg(self, event):
        p = self.clean_drop_path(event)
        self.bg_file_var.set(p)
        
    def open_result_folder(self):
        path = self.ai_status.get()
        # If it's a message like "Procesando...", ignore
        if not os.path.isabs(path): 
             path = os.getcwd()
             
        if os.path.exists(path):
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
            else:
                os.startfile(path)
        else:
             os.startfile(os.getcwd())

    def update_ai_status(self, text, is_success=False):
        self.ai_status.delete(0, "end")
        self.ai_status.insert(0, text)
        if is_success:
             self.ai_status.configure(text_color=DOWNMESS_GREEN)
        else:
             self.ai_status.configure(text_color="white")

    def select_single_file(self, str_var):
        f = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff")])
        if f: str_var.set(f)

    def start_resize_thread(self):
        threading.Thread(target=self.run_resize, daemon=True).start()

    def run_resize(self):
        f = self.resize_file_var.get()
        if not os.path.exists(f): return
        
        try:
            w = int(self.resize_w.get())
            h = int(self.resize_h.get())
            self.update_ai_status("Procesando...", False)
            
            out = self.core.resize_image(f, w, h)
            
            self.update_ai_status(out, True)
            self.core.send_notification("Downmess", "Rescalado completado")
        except Exception as e:
            self.update_ai_status(f"Error: {e}", False)

    def start_upscale_thread(self):
        threading.Thread(target=self.run_upscale, daemon=True).start()
        
    def run_upscale(self):
        f = self.upscale_file_var.get()
        if not os.path.exists(f): return
        
        try:
            model = self.ai_model_var.get()
            scale = int(self.ai_scale_var.get())
            
            self.update_ai_status("Descargando modelo/Procesando...", False)
            
            out = self.core.upscale_image_ai(f, model=model, scale=scale)
            
            self.update_ai_status(out, True)
            self.core.send_notification("Downmess", "Mejora IA completada")
        except Exception as e:
             self.update_ai_status(f"Error: {e}", False)

    def start_bg_remove_thread(self):
        threading.Thread(target=self.run_bg_remove, daemon=True).start()

    def run_bg_remove(self):
        f = self.bg_file_var.get()
        if not os.path.exists(f): return
        
        try:
            self.update_ai_status("Eliminando fondo...", False)
            out = self.core.remove_background(f)
            self.update_ai_status(out, True)
            self.core.send_notification("Downmess", "Fondo eliminado con éxito")
        except Exception as e:
             self.update_ai_status(f"Error: {e}", False)

if __name__ == "__main__":
    app = DownmessApp()
    app.mainloop()
