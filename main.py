import sys
import os
import tkinter as tk
from tkinter import ttk

# ==========================================================
# PATH INJECTION: MUST BE DONE BEFORE IMPORTING SUB-APPS
# ==========================================================
base_path = os.path.dirname(os.path.abspath(__file__))
subfolders = ["Cloud_File_Manager", "Github_Notifier", "OCR_Clipboard_Utility"]

for folder in subfolders:
    full_path = os.path.join(base_path, folder)
    if os.path.exists(full_path):
        sys.path.insert(0, full_path)

try:
    from Cloud_File_Manager.main import CloudManagerApp
    from Github_Notifier.main import GithubNotifierApp
    from OCR_Clipboard_Utility.main import OcrApp
except ImportError as e:
    print(f"Critical Import Error: {e}")

# ==========================================================
# MAIN HUB GUI CLASS
# ==========================================================
class AutomationHub(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Automation Hub v1.0")
        self.geometry("1300x850")
        self.configure(bg="#f5f6fa")

        # State Tracking
        self.loaded_features = {}
        self.nav_buttons = {}  # Store button references for highlighting
        self.current_feature_instance = None

        # Sidebar
        self.sidebar = tk.Frame(self, width=250, bg="#2f3640")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="AUTOMATION HUB", fg="white", bg="#2f3640",
                 font=("Segoe UI", 16, "bold"), pady=30).pack()

        # Main Display Area
        self.display_area = tk.Frame(self, bg="white", highlightbackground="#dcdde1", highlightthickness=1)
        self.display_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.placeholder_label = tk.Label(self.display_area,
                                          text="Welcome to the Hub\nSelect a feature to get started",
                                          font=("Segoe UI", 14), fg="#7f8c8d", bg="white")
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

        self.create_nav_buttons()

    def create_nav_buttons(self):
        features = [
            ("Cloud File Manager", CloudManagerApp, "cloud"),
            ("GitHub Notifier", GithubNotifierApp, "github"),
            ("OCR Utility", OcrApp, "ocr")
        ]

        for text, app_class, key in features:
            btn = tk.Button(self.sidebar, text=text,
                            font=("Segoe UI", 11),
                            bg="#353b48", fg="white",
                            activebackground="#4a69bd", activeforeground="white",
                            bd=0, pady=15, cursor="hand2",
                            command=lambda c=app_class, k=key: self.load_feature(c, k))
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[key] = btn # Store button for color swapping

        tk.Button(self.sidebar, text="Exit Hub", bg="#c23616", fg="white", bd=0,
                  command=self.quit, pady=10).pack(side="bottom", fill="x", padx=10, pady=20)

    def load_feature(self, app_class, key):
        # 1. Update Button Highlighting
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.config(bg="#4a69bd") # Selected color (Blue)
            else:
                btn.config(bg="#353b48") # Default color

        # 2. Manage Display Area
        if self.placeholder_label:
            self.placeholder_label.place_forget()

        if self.current_feature_instance:
            self.current_feature_instance.pack_forget()

        # 3. Lazy Load / State Persistence
        if key not in self.loaded_features:
            try:
                # FIXED: Removed the undefined 'text' variable here
                new_instance = app_class(self.display_area)
                self.loaded_features[key] = new_instance
            except Exception as e:
                error_msg = tk.Label(self.display_area, text=f"Error initializing {key}: {e}", fg="red")
                error_msg.pack(pady=20)
                return

        # 4. Show instance
        self.current_feature_instance = self.loaded_features[key]
        self.current_feature_instance.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AutomationHub()
    app.mainloop()