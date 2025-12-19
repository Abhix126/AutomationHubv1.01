import pytesseract
import pyperclip
import time
import io
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image
from hashlib import sha256
import webbrowser
import psutil

# Configuration File Path
CONFIG_FILE = 'ocr_config.txt'
VBSCRIPT_FILENAME = 'ask.vbs'
DEFAULT_TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# CHANGED: Now inherits from tk.Frame
class OcrApp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.root = parent

        # State variables
        self.tesseract_path = tk.StringVar(self)
        self.is_scanning = False
        self.scanner_thread = None
        self.last_image_hash = None
        self.scan_interval = 1.0

        # Initialize psutil
        try:
            self.process = psutil.Process(os.getpid())
        except psutil.NoSuchProcess:
            self.process = None

        # Initialize UI and load settings
        self.load_config()
        self.create_widgets()

        # Ensure Tesseract path is configured on startup
        self.configure_tesseract()

        # Start the performance monitoring loop
        self.update_system_stats()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    path = f.read().strip()
                    if path:
                        self.tesseract_path.set(path)
            except Exception:
                self.tesseract_path.set(DEFAULT_TESSERACT_PATH)
        else:
            self.tesseract_path.set(DEFAULT_TESSERACT_PATH)

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.write(self.tesseract_path.get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def create_widgets(self):
        # --- Tesseract Path Entry ---
        path_frame = tk.Frame(self, padx=10, pady=10)
        path_frame.pack(fill='x')

        tk.Label(path_frame, text="Tesseract Path:", font=('Arial', 10, 'bold')).pack(anchor='w')

        self.path_entry = tk.Entry(path_frame, textvariable=self.tesseract_path, width=50)
        self.path_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        browse_button = tk.Button(path_frame, text="Browse", command=self.browse_tesseract)
        browse_button.pack(side='right')

        save_button = tk.Button(path_frame, text="Save Path", command=self.configure_tesseract)
        save_button.pack(side='right', padx=(5, 0))

        # --- Activation Button ---
        self.toggle_button = tk.Button(self, text="Activate Scanner",
                                       command=self.toggle_scanner,
                                       bg='green', fg='white',
                                       font=('Arial', 12, 'bold'),
                                       padx=10, pady=5)
        self.toggle_button.pack(pady=20)

        # --- Status Display ---
        self.status_label = tk.Label(self, text="Status: Ready.",
                                     font=('Arial', 10), bd=1, relief='sunken', anchor='w')
        self.status_label.pack(fill='x', padx=10, pady=(0, 10), ipady=5)

        # --- System Monitoring Stats ---
        monitoring_frame = tk.Frame(self, padx=10, pady=5)
        monitoring_frame.pack(fill='x')

        tk.Label(monitoring_frame, text="Performance:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.cpu_label = tk.Label(monitoring_frame, text="CPU: 0.0%", font=('Arial', 9))
        self.cpu_label.pack(side=tk.LEFT, padx=(0, 15))
        self.ram_label = tk.Label(monitoring_frame, text="RAM: 0.0 MB", font=('Arial', 9))
        self.ram_label.pack(side=tk.LEFT)

        # --- Guidance Text ---
        disclaimer_text = (
            "⚠️ Accuracy Guidance\n"
            "For maximum accuracy, use images that are primarily text on a clean background."
        )
        self.disclaimer_label = tk.Label(self, text=disclaimer_text,
                                         font=('Arial', 9, 'italic'),
                                         fg='darkblue', wraplength=400, justify=tk.LEFT)
        self.disclaimer_label.pack(fill='x', padx=10, pady=10)

        # --- Footer ---
        footer_frame = tk.Frame(self, padx=10, pady=5)
        footer_frame.pack(fill='x', side=tk.BOTTOM)

        tk.Label(footer_frame, text="© 2025 Clipboard OCR Utility", font=('Arial', 8)).pack(side=tk.LEFT)
        tk.Button(footer_frame, text="Contact Support", command=self.open_support_email,
                  font=('Arial', 8), relief=tk.FLAT, fg='blue').pack(side=tk.LEFT)

    def open_support_email(self):
        webbrowser.open("mailto:abhijitsahascience@gmail.com")

    def browse_tesseract(self):
        filepath = filedialog.askopenfilename(title="Select tesseract.exe", filetypes=[("Executable Files", "tesseract.exe")])
        if filepath:
            self.tesseract_path.set(filepath)
            self.configure_tesseract()

    def configure_tesseract(self):
        path = self.tesseract_path.get()
        if not path or not os.path.exists(path):
            self.update_status(f"Error: Path invalid.", 'red')
            return False
        try:
            pytesseract.pytesseract.tesseract_cmd = path
            self.save_config()
            self.update_status(f"Tesseract configured.", 'blue')
            return True
        except Exception as e:
            self.update_status(f"Failed: {e}", 'red')
            return False

    def update_status(self, message, color='black'):
        self.status_label.config(text=f"Status: {message}", fg=color)

    def update_system_stats(self):
        if self.process:
            try:
                cpu_usage = self.process.cpu_percent()
                ram_mb = self.process.memory_info().rss / (1024 * 1024)
                self.cpu_label.config(text=f"CPU: {cpu_usage:.1f}%")
                self.ram_label.config(text=f"RAM: {ram_mb:.1f} MB")
            except:
                pass
        self.after(1000, self.update_system_stats)

    def toggle_scanner(self):
        if not self.configure_tesseract(): return
        if self.is_scanning:
            self.is_scanning = False
            self.toggle_button.config(text="Activate Scanner", bg='green')
        else:
            self.is_scanning = True
            self.scanner_thread = threading.Thread(target=self.continuous_ocr_loop, daemon=True)
            self.scanner_thread.start()
            self.toggle_button.config(text="Deactivate Scanner", bg='red')

    def get_clipboard_image(self):
        try:
            img = ImageGrab.grabclipboard()
            return img if isinstance(img, Image.Image) else None
        except: return None

    def calculate_image_hash(self, img):
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')
        return sha256(byte_arr.getvalue()).hexdigest()

    def perform_ocr(self, img):
        configs = [r'--oem 3 --psm 6', r'--oem 3 --psm 3']
        for config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config).strip()
                if text: return text
            except: continue
        return None

    def run_prompt(self):
        # Locate VBScript relative to this file's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, VBSCRIPT_FILENAME)
        try:
            process = subprocess.run(['cscript', '//Nologo', script_path], capture_output=True, text=True, timeout=30)
            return process.stdout.strip()
        except: return '7'

    def continuous_ocr_loop(self):
        self.last_image_hash = None
        while self.is_scanning:
            try:
                current_img = self.get_clipboard_image()
                if current_img:
                    current_hash = self.calculate_image_hash(current_img)
                    if current_hash != self.last_image_hash:
                        res = self.run_prompt()
                        if res == '6':
                            text = self.perform_ocr(current_img)
                            if text:
                                pyperclip.copy(text)
                                self.last_image_hash = current_hash
                                self.after(0, lambda: self.update_status("Text copied!", 'green'))
                        else:
                            self.last_image_hash = current_hash
                time.sleep(self.scan_interval)
            except:
                time.sleep(5)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("OCR Utility Standalone")
    root.geometry("450x480")
    app = OcrApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()