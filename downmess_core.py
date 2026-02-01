import os
import json
import subprocess
import yt_dlp
from datetime import datetime
from plyer import notification

# Constants
HISTORY_FILE = "downmess_history.json"
SEARCH_HISTORY_FILE = "search_history.json"

class DownmessCore:
    def __init__(self):
        self.history = self.load_history()
        self.search_history = self.load_search_history()

    # --- History Logic ---
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f: return json.load(f)
            except: return []
        return []

    def add_history(self, title, url, quality):
        entry = {
            "title": title,
            "url": url,
            "quality": quality,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, entry) # Prepend
        try:
            with open(HISTORY_FILE, 'w') as f: json.dump(self.history, f, indent=4)
        except: pass

    def load_search_history(self):
        if os.path.exists(SEARCH_HISTORY_FILE):
            try:
                with open(SEARCH_HISTORY_FILE, 'r') as f: return json.load(f)
            except: return []
        return []

    def add_search_history(self, query):
        if not query: return
        # Remove if exists to move to top
        if query in self.search_history:
            self.search_history.remove(query)
        
        self.search_history.insert(0, query)
        # Limit to 20
        self.search_history = self.search_history[:20]
        
        try:
            with open(SEARCH_HISTORY_FILE, 'w') as f: json.dump(self.search_history, f)
        except: pass

    def clear_search_history(self):
        self.search_history = []
        try:
            if os.path.exists(SEARCH_HISTORY_FILE):
                os.remove(SEARCH_HISTORY_FILE)
        except: pass

    # --- Download Logic ---
    def download_url(self, url, quality, normalize=False, progress_hook=None, start_time=None, end_time=None):
        """
        Downloads URL with specified quality.
        normalize: If True, applies EBU R128 audio normalization.
        start_time/end_time: Format "HH:MM:SS" or "MM:SS" or seconds.
        """
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [progress_hook] if progress_hook else [],
            'quiet': True,
            'no_warnings': True,
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            'force_overwrites': True
        }

        # Time Range Support (Using yt-dlp download_sections)
        if start_time or end_time:
            # Basic validation/cleanup of time format
            s = start_time if start_time else "0"
            e = end_time if end_time else "99:59:59" # Large enough
            
            # Use download_sections to only download the specific part
            # Syntax: *[start-end]
            ydl_opts['download_sections'] = [{
                'start_time': self._parse_time_to_seconds(s),
                'end_time': self._parse_time_to_seconds(e),
                'title': 'section'
            }]
            # Important for sections to work without downloading the whole file first (if server supports range)
            ydl_opts['concurrent_fragment_downloads'] = 1 

        # Quality Configuration
        if quality == "Mejor Calidad (4K/8K)":
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "720p":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "Solo Audio (MP3 320kbps)":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        elif quality == "Solo Audio (WAV)":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]

        # Folder Organization
        is_audio = "Audio" in quality or "MP3" in quality or "WAV" in quality
        folder_name = "Musica" if is_audio else "Videos"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        ydl_opts['outtmpl'] = f'{folder_name}/%(title)s.%(ext)s'

        # Variables to store info for post-processing
        downloaded_info = None
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                downloaded_info = ydl.extract_info(url, download=True)
        except Exception as e:
            print(f"Download Error: {e}")
            return None

        if not downloaded_info:
            return None

        title = downloaded_info.get('title', 'Unknown')
        
        # Post-Download Normalization (Manual FFmpeg to avoid yt-dlp errors)
        # Moved OUTSIDE the with context to ensure file handles are released
        if normalize:
            try:
                # Use a fresh yt-dlp instance or simple logic to guess filename if needed, 
                # but better to capture it inside or use the dict. 
                # Re-instantiating solely for prepare_filename is safer.
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    filepath = ydl.prepare_filename(downloaded_info)
                
                # Fix extension if merged
                if quality in ["Mejor Calidad (4K/8K)", "1080p", "720p"] and not filepath.endswith(".mp4"):
                    filepath = os.path.splitext(filepath)[0] + ".mp4"
                elif quality == "Solo Audio (MP3 320kbps)" and not filepath.endswith(".mp3"):
                        filepath = os.path.splitext(filepath)[0] + ".mp3"
                elif quality == "Solo Audio (WAV)" and not filepath.endswith(".wav"):
                        filepath = os.path.splitext(filepath)[0] + ".wav"

                if os.path.exists(filepath):
                    self.normalize_audio_manual(filepath)
            except Exception as e:
                print(f"Normalization Error: {e}")

        # Final Validation: Check if file exists
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                final_path = ydl.prepare_filename(downloaded_info)
            
            # Helper to find actual file if extension changed
            if not os.path.exists(final_path):
                # Try common extensions if main path missing
                base = os.path.splitext(final_path)[0]
                for ext in ['.mp4', '.mp3', '.wav', '.mkv', '.webm']:
                    if os.path.exists(base + ext):
                        final_path = base + ext
                        break
            
            if not os.path.exists(final_path):
                 print(f"Validation Error: File not found at {final_path}")
                 # We return None to indicate failure to the UI
                 return None
                 
        except Exception: 
            pass

        self.add_history(title, url, quality)
        return title

    def _parse_time_to_seconds(self, time_str):
        """Helper to convert HH:MM:SS or MM:SS to total seconds."""
        if not time_str: return 0
        try:
            parts = str(time_str).split(':')
            if len(parts) == 3: # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2: # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            else: # Seconds
                return int(parts[0])
        except:
            return 0

    def normalize_audio_manual(self, filepath):
        """Applies EBU R128 normalization using ffmpeg manually."""
        temp_file = f"{filepath}.tmp{os.path.splitext(filepath)[1]}"
        
        # Determine codecs based on file extension
        ext = os.path.splitext(filepath)[1].lower()
        
        cmd = ['ffmpeg', '-y', '-i', filepath]
        
        if ext in ['.mp4', '.mkv', '.avi', '.mov']:
            cmd.extend(['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k'])
        elif ext == '.mp3':
            cmd.extend(['-vn', '-acodec', 'libmp3lame', '-q:a', '2'])
        elif ext == '.wav':
             cmd.extend(['-vn', '-acodec', 'pcm_s16le'])
        
        cmd.extend(['-filter:a', 'loudnorm=I=-16:TP=-1.5:LRA=11', temp_file])
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Replace original with normalized (Retry logic for Windows)
        if os.path.exists(temp_file):
            import time
            for attempt in range(5):
                try:
                    os.replace(temp_file, filepath)
                    break
                except PermissionError:
                    time.sleep(1.0)
                except Exception as e:
                    print(f"Error replacing file: {e}")
                    break

    # --- Search Logic ---
    def search_videos(self, query, limit=10, engine="ytsearch"):
        """
        Searches using yt-dlp with specific engine (ytsearch, scsearch).
        """
        ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': True, 
            'default_search': engine,
            'noplaylist': True,
        }
        
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Use engine prefix explicitly to be safe
                search_term = f"{engine}{limit}:{query}"
                info = ydl.extract_info(search_term, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        results.append({
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url', ''),
                            'thumbnail': entry.get('thumbnail', ''),
                            'duration': entry.get('duration', 0),
                            'uploader': entry.get('uploader', '')
                        })
        except Exception as e:
            print(f"Search Error: {e}")
            
        return results

    # --- Converter Logic ---
    def convert_file(self, file_path, target_format, normalize=False):
        """
        Converts file to target_format using ffmpeg directly.
        normalize: If True, applies EBU R128 audio normalization.
        """
        base_name = os.path.splitext(file_path)[0]
        output_file = f"{base_name}_converted.{target_format}"
        
        cmd = ['ffmpeg', '-y', '-i', file_path]
        
        # Mapping Extended
        tf = target_format.lower()
        
        # Audio
        if tf == "mp3":
            cmd.extend(['-vn', '-acodec', 'libmp3lame', '-q:a', '2'])
        elif tf == "wav":
            cmd.extend(['-vn', '-acodec', 'pcm_s16le'])
        elif tf == "flac":
            cmd.extend(['-vn', '-acodec', 'flac'])
        elif tf == "ogg":
            cmd.extend(['-vn', '-acodec', 'libvorbis', '-q:a', '6'])
        elif tf == "m4a":
            cmd.extend(['-vn', '-acodec', 'aac', '-b:a', '192k'])
            
        # Video
        elif tf == "mp4":
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental'])
        elif tf == "avi":
            cmd.extend(['-c:v', 'mpeg4', '-c:a', 'mp3'])
        elif tf == "mkv":
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
        elif tf == "mov":
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        elif tf == "gif":
            cmd.extend(['-vf', 'fps=10,scale=320:-1:flags=lanczos'])
            
        # Images
        elif tf in ["png", "jpg", "jpeg", "webp", "tiff", "bmp", "ico"]:
             # Basic image conversion
             pass 
        
        # Normalization (Audio/Video only)
        if normalize and tf not in ["gif", "png", "jpg", "jpeg", "webp", "tiff", "bmp", "ico"]:
             cmd.extend(['-filter:a', 'loudnorm=I=-16:TP=-1.5:LRA=11'])
            
        cmd.append(output_file)
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_file

    # --- Image & AI Tools ---
    def resize_image(self, file_path, width, height):
        import cv2
        img = cv2.imread(file_path)
        if img is None: raise Exception("No se pudo leer la imagen")
        
        resized = cv2.resize(img, (int(width), int(height)), interpolation=cv2.INTER_LANCZOS4)
        
        output_path = f"{os.path.splitext(file_path)[0]}_resized_{width}x{height}.png"
        cv2.imwrite(output_path, resized)
        return output_path

    def upscale_image_ai(self, file_path, model="edsr", scale=4):
        import cv2
        from cv2 import dnn_superres
        import numpy as np
        
        # Validation
        valid_models = ["edsr", "espcn", "fsrcnn", "lapsrn"]
        if model not in valid_models: model = "edsr"
        
        # Model Path Management
        model_filename = f"{model.upper()}_x{scale}.pb"
        model_path = os.path.join(os.getcwd(), "models", model_filename)
        
        if not os.path.exists(os.path.dirname(model_path)):
            os.makedirs(os.path.dirname(model_path))
            
        if not os.path.exists(model_path):
             self.download_model(model, scale, model_path)
             
        # Inference
        sr = dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        sr.setModel(model, scale)
        
        img = cv2.imread(file_path)
        if img is None: raise Exception("No se pudo leer la imagen")
        
        h, w = img.shape[:2]
        
        # Tiling Logic for Memory Optimization (if image > 1000px on any side)
        TILE_SIZE = 512
        if w > 1000 or h > 1000:
            new_h, new_w = h * scale, w * scale
            output_img = np.zeros((new_h, new_w, 3), dtype=np.uint8)
            
            for y in range(0, h, TILE_SIZE):
                for x in range(0, w, TILE_SIZE):
                    # Crop
                    h_slice = min(y+TILE_SIZE, h) - y
                    w_slice = min(x+TILE_SIZE, w) - x
                    roi = img[y:y+h_slice, x:x+w_slice]
                    
                    # Upscale
                    upscaled_roi = sr.upsample(roi)
                    
                    # Place
                    out_y, out_x = y * scale, x * scale
                    out_h_slice, out_w_slice = upscaled_roi.shape[:2]
                    output_img[out_y:out_y+out_h_slice, out_x:out_x+out_w_slice] = upscaled_roi
                    
            upscaled = output_img
        else:
            upscaled = sr.upsample(img)
        
        output_path = f"{os.path.splitext(file_path)[0]}_AI_x{scale}.png"
        cv2.imwrite(output_path, upscaled)
        return output_path

    def download_model(self, model, scale, path):
        import urllib.request
        # Using a reliable mirror for opencv models
        url_map = {
            "edsr": f"https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x{scale}.pb",
            "espcn": f"https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x{scale}.pb",
            "fsrcnn": f"https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x{scale}.pb",
            "lapsrn": f"https://github.com/fannymonori/TF-LapSRN/raw/master/export/LapSRN_x{scale}.pb" 
        }
        
        url = url_map.get(model)
        if not url:
             url = f"https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x{scale}.pb"

        print(f"Downloading AI Model: {url}...")
        urllib.request.urlretrieve(url, path)

    def remove_background(self, file_path):
        from rembg import remove
        from PIL import Image
        
        if not os.path.exists(file_path): raise Exception("Archivo no encontrado")
        
        input_img = Image.open(file_path)
        output_img = remove(input_img)
        
        output_path = f"{os.path.splitext(file_path)[0]}_nobg.png"
        output_img.save(output_path)
        
        return output_path

    # --- Audio Analysis (AI) ---
    def analyze_audio(self, file_path):
        import librosa
        import numpy as np
        import matplotlib.pyplot as plt
        import io
        
        try:
            # 1. Load Audio
            y, sr = librosa.load(file_path, duration=60) # Analyze first 60s for speed
            
            # 2. BPM (Tempo)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            bpm = round(tempo, 1) if isinstance(tempo, float) else round(tempo[0], 1)
            
            # 3. Key Detection (Simple Chroma)
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_vals = np.sum(chroma, axis=1)
            notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_idx = np.argmax(chroma_vals)
            key = notes[key_idx]
            
            # 4. Waveform Image
            plt.figure(figsize=(6, 2), facecolor='black')
            librosa.display.waveshow(y, sr=sr, color='#00F3FF', alpha=0.8)
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='black')
            buf.seek(0)
            plt.close()
            
            return {
                "bpm": bpm,
                "key": key,
                "waveform": buf.read() # Bytes of the PNG
            }
            
        except Exception as e:
            print(f"Analysis Error: {e}")
            raise e
            
    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Downmess',
                timeout=5
            )
        except Exception:
            pass
