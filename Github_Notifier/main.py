import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import re
import requests
import sys
import os  # Added for path handling
import time
import urllib.parse
import io

# Keeping your original imports
from creds import GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET, GITHUB_OWNER, GITHUB_REPO
from github_webhook_server import app  # Flask app

# Constants
LOCAL_PORT = 5000
ENDPOINT_PATH = "/github-webhook"
CLOUDFLARED_START_TIMEOUT = 30


class GithubNotifierApp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = False
        self.proc = None
        self.hook_id = None

        self.setup_gui()

    def setup_gui(self):
        # --- Control Header ---
        header = tk.Frame(self, pady=10)
        header.pack(fill=tk.X)

        self.status_label = tk.Label(header, text="Status: INACTIVE", fg="red", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=20)

        self.toggle_btn = tk.Button(header, text="ACTIVATE TUNNEL", bg="#27ae60", fg="white",
                                    font=("Arial", 10, "bold"), command=self.toggle_service, width=20)
        self.toggle_btn.pack(side=tk.RIGHT, padx=20)

        # --- Terminal Area ---
        terminal_frame = tk.LabelFrame(self, text="Tunnel & Webhook Log", padx=5, pady=5)
        terminal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.console = tk.Text(terminal_frame, bg="black", fg="#00FF00", font=("Consolas", 10),
                               insertbackground="#00FF00", state="disabled", wrap="word")
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(terminal_frame, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console["yscrollcommand"] = scrollbar.set

    def log(self, message):
        """Custom log function to write to the GUI terminal"""
        self.console.config(state="normal")
        self.console.insert(tk.END, f"{message}\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def toggle_service(self):
        if not self.running:
            self.start_service()
        else:
            self.stop_service()

    def start_service(self):
        self.running = True
        self.toggle_btn.config(text="DEACTIVATE", bg="#c0392b")
        self.status_label.config(text="Status: STARTING...", fg="orange")
        self.log("🚀 Initializing system...")

        # Run core logic in a separate thread
        threading.Thread(target=self.core_logic_thread, daemon=True).start()

    def stop_service(self):
        self.log("\n🛑 Shutting down...")
        try:
            if self.hook_id:
                delete_github_webhook(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN, self.hook_id)
                self.log("✅ Webhook deleted from GitHub.")
            if self.proc:
                self.proc.terminate()
                self.log("🔌 Tunnel closed.")
        except Exception as e:
            self.log(f"⚠️ Shutdown error: {e}")

        self.running = False
        self.toggle_btn.config(text="ACTIVATE TUNNEL", bg="#27ae60")
        self.status_label.config(text="Status: INACTIVE", fg="red")

    def core_logic_thread(self):
        try:
            # 1. Start Tunnel
            self.log("📡 Opening Cloudflared tunnel...")
            self.proc, public_url = start_cloudflared_and_get_public_url(self.log)
            self.log(f"✅ Public URL: {public_url}")

            # 2. Create Webhook
            full_webhook_url = public_url + ENDPOINT_PATH
            self.hook_id = create_github_webhook(GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN, full_webhook_url,
                                                 GITHUB_WEBHOOK_SECRET)
            self.log(f"✅ Webhook created (ID: {self.hook_id})")

            # 3. Start Flask
            self.status_label.config(text="Status: ACTIVE (Listening)", fg="#27ae60")
            threading.Thread(target=run_flask, daemon=True).start()
            self.log("🟢 System online. Listening for events...")

            # OPTIONAL: Test notification on startup
            # self.run_vb_notify("System Active", "GitHub Notifier is now monitoring your repo.")

        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {e}")
            self.stop_service()

    def run_vb_notify(self, title, message):
        """Triggers the VBScript notification to show on top of all windows."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vbs_path = os.path.join(script_dir, "notify.vbs")

        # If the vbs file doesn't exist, create a temporary one
        if not os.path.exists(vbs_path):
            with open(vbs_path, "w") as f:
                # 4096 = System Modal (Always on Top)
                f.write(f'MsgBox "{message}", 0 + 64 + 4096, "{title}"')

        def _trigger():
            subprocess.run(['cscript', '//Nologo', vbs_path], shell=True)

        threading.Thread(target=_trigger, daemon=True).start()


# --- REFACTORED CORE LOGIC ---

def start_cloudflared_and_get_public_url(log_func) -> tuple:
    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{LOCAL_PORT}", "--loglevel", "info"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    public_url = None
    url_regex = re.compile(r'https://[^\s\)\]\}\,\'"]+')
    deadline = time.time() + CLOUDFLARED_START_TIMEOUT

    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None: break
        if line:
            log_func(f"[cloudflared] {line.strip()}")
            urls = url_regex.findall(line)
            for url in urls:
                clean_url = _sanitize_url_candidate(url)
                if clean_url:
                    public_url = clean_url
                    break
        if public_url: break

    if not public_url:
        proc.terminate()
        raise RuntimeError("Failed to get public URL.")
    return proc, public_url.rstrip("/")


def _sanitize_url_candidate(raw_url: str) -> str:
    if not raw_url: return None
    raw_url = raw_url.strip().rstrip('.,);\'"')
    parsed = urllib.parse.urlparse(raw_url)
    if parsed.scheme != "https": return None
    hostname = parsed.hostname or ""
    if not (hostname.endswith(".trycloudflare.com") or hostname.endswith(".cloudflare-tunnel.com")):
        return None
    return urllib.parse.urlunparse(parsed._replace(path="", params="", query="", fragment=""))


def create_github_webhook(owner, repo, token, webhook_url, secret):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "name": "web", "active": True, "events": ["*"],
        "config": {"url": webhook_url, "content_type": "json", "secret": secret, "insecure_ssl": "0"}
    }
    resp = requests.post(api_url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json().get("id")


def delete_github_webhook(owner, repo, token, hook_id):
    url = f"https://api.github.com/repos/{owner}/{repo}/hooks/{hook_id}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    requests.delete(url, headers=headers).raise_for_status()


def run_flask():
    app.run(host="0.0.0.0", port=LOCAL_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Standalone GitHub Notifier")
    root.geometry("800x500")
    app_gui = GithubNotifierApp(root)
    app_gui.pack(fill="both", expand=True)
    root.mainloop()