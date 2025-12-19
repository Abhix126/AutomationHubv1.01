import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import webbrowser
import threading


# Keeping your original imports
from s3_manager import S3Manager
from local_manager import list_local_items
from logger import AppLogger



# CHANGED: Inherit from tk.Frame instead of a generic object
class CloudManagerApp(tk.Frame):
    def __init__(self, parent):
        # CHANGED: Initialize the Frame
        super().__init__(parent)
        self.root = parent

        # NOTE: Geometry and Title removed from here as they are now
        # controlled by the Main Hub.

        self.s3 = S3Manager()

        # --- Split Panes ---
        # CHANGED: Attached to 'self' (the frame) instead of root
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Local Side
        self.local_frame = ttk.Frame(self.paned, padding=5)
        self.local_tree = ttk.Treeview(self.local_frame, selectmode="extended")
        self.local_tree.pack(fill=tk.BOTH, expand=True)
        self.local_tree.heading("#0", text="Local Filesystem", anchor="w")
        self.populate_local_root()
        self.local_tree.bind("<<TreeviewOpen>>", self.expand_local_node)
        self.paned.add(self.local_frame, weight=1)

        # S3 Side
        self.s3_frame = ttk.Frame(self.paned, padding=5)
        self.s3_tree = ttk.Treeview(self.s3_frame, selectmode="extended")
        self.s3_tree.pack(fill=tk.BOTH, expand=True)
        self.s3_tree.heading("#0", text="S3 Bucket", anchor="w")
        self.populate_s3_root()
        self.s3_tree.bind("<<TreeviewOpen>>", self.expand_s3_node)
        self.paned.add(self.s3_frame, weight=1)

        # --- Bottom Panel ---
        # CHANGED: Attached to 'self'
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(self.bottom_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Upload → S3", command=self.upload_to_s3).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Download from S3", command=self.download_from_s3).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create S3 Folder", command=self.create_s3_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete S3 Object(s)", command=self.delete_s3_objects).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Object (URL)", command=self.view_object_url).pack(side=tk.LEFT, padx=5)

        # --- Progress Bar ---
        progress_frame = ttk.LabelFrame(self.bottom_frame, text="Progress", padding=5)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("green.Horizontal.TProgressbar", background="#00FF00", troughcolor="black", thickness=20)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # --- Log Console ---
        console_frame = ttk.LabelFrame(self.bottom_frame, text="Activity Log", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.console = tk.Text(console_frame, bg="black", fg="#00FF00", insertbackground="#00FF00",
                               state="disabled", wrap="word")
        self.console.pack(fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(console_frame, command=self.console.yview)
        self.console["yscrollcommand"] = self.scrollbar.set
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initialize logger
        self.logger = AppLogger(self.console)
        self.logger.log("Application started successfully.")

    # ---------------- Local Logic (No Changes) ----------------
    def populate_local_root(self):
        drives = []
        if os.name == "nt":
            import string
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            drives = ["/"]

        for drive in drives:
            node = self.local_tree.insert("", tk.END, text=drive, values=[drive], open=False)
            self.local_tree.insert(node, tk.END, text="Loading...")

    def expand_local_node(self, event):
        node = self.local_tree.focus()
        path = self.local_tree.item(node, "values")[0]
        self.local_tree.delete(*self.local_tree.get_children(node))
        folders, files = list_local_items(path)
        for folder in folders:
            folder_path = os.path.join(path, folder)
            child = self.local_tree.insert(node, tk.END, text=folder, values=[folder_path])
            self.local_tree.insert(child, tk.END, text="Loading...")
        for file in files:
            file_path = os.path.join(path, file)
            self.local_tree.insert(node, tk.END, text=file, values=[file_path])

    # ---------------- S3 Logic (No Changes) ----------------
    def populate_s3_root(self):
        folders, files = self.s3.list_prefix("")
        for f in folders:
            node = self.s3_tree.insert("", tk.END, text=f, values=[f])
            self.s3_tree.insert(node, tk.END, text="Loading...")
        for file in files:
            self.s3_tree.insert("", tk.END, text=file, values=[file])

    def expand_s3_node(self, event):
        node = self.s3_tree.focus()
        prefix = self.s3_tree.item(node, "values")[0]
        self.s3_tree.delete(*self.s3_tree.get_children(node))
        folders, files = self.s3.list_prefix(prefix)
        for f in folders:
            child = self.s3_tree.insert(node, tk.END, text=f.split("/")[-2], values=[f])
            self.s3_tree.insert(child, tk.END, text="Loading...")
        for file in files:
            self.s3_tree.insert(node, tk.END, text=file.split("/")[-1], values=[file])

    # ---------------- Progress ----------------
    def update_progress(self, completed, total):
        if total == 0:
            return
        percent = (completed / total) * 100
        self.progress_var.set(percent)
        self.update_idletasks()  # CHANGED: Called on self

    def reset_progress(self):
        self.progress_var.set(0)
        self.update_idletasks()  # CHANGED: Called on self

    # ---------------- Actions (No Changes) ----------------
    def threaded_action(self, func, *args):
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()

    def upload_to_s3(self):
        self.threaded_action(self._upload_to_s3_internal)

    def _upload_to_s3_internal(self):
        selected_local_nodes = self.local_tree.selection()
        if not selected_local_nodes:
            messagebox.showwarning("Select Files", "Please select one or more local files.")
            return

        selected_s3_nodes = self.s3_tree.selection()
        s3_prefix = ""
        if selected_s3_nodes:
            target_node = selected_s3_nodes[0]
            target_key = self.s3_tree.item(target_node, "values")[0]
            if target_key.endswith("/"):
                s3_prefix = target_key
            else:
                parent_node = self.s3_tree.parent(target_node)
                s3_prefix = self.s3_tree.item(parent_node, "values")[0] if parent_node else ""

        total = len(selected_local_nodes)
        completed = 0

        for node in selected_local_nodes:
            local_path = self.local_tree.item(node, "values")[0]
            if os.path.isdir(local_path):
                continue
            filename = os.path.basename(local_path)
            s3_path = f"{s3_prefix}{filename}"
            self.s3.upload_file(local_path, s3_path)
            completed += 1
            self.update_progress(completed, total)
            self.logger.log(f"Uploaded: {local_path} → s3://{self.s3.bucket}/{s3_path}")

        self.logger.log(f"Upload complete: {completed}/{total} file(s).")
        self.reset_progress()
        self.refresh_s3_tree()

    def download_from_s3(self):
        self.threaded_action(self._download_from_s3_internal)

    def _download_from_s3_internal(self):
        selected_nodes = self.s3_tree.selection()
        if not selected_nodes:
            messagebox.showwarning("Select Files", "Select one or more S3 objects to download.")
            return

        folder = filedialog.askdirectory(title="Select Local Folder to Save Files")
        if not folder:
            return

        total = len(selected_nodes)
        completed = 0

        for node in selected_nodes:
            s3_key = self.s3_tree.item(node, "values")[0]
            local_path = os.path.join(folder, os.path.basename(s3_key))
            self.s3.download_file(s3_key, local_path)
            completed += 1
            self.update_progress(completed, total)
            self.logger.log(f"Downloaded: s3://{self.s3.bucket}/{s3_key} → {local_path}")

        self.logger.log(f"Download complete: {completed}/{total} file(s).")
        self.reset_progress()

    def delete_s3_objects(self):
        self.threaded_action(self._delete_s3_objects_internal)

    def _delete_s3_objects_internal(self):
        selected_nodes = self.s3_tree.selection()
        if not selected_nodes:
            messagebox.showwarning("Select Files", "Select one or more S3 objects to delete.")
            return

        keys = [self.s3_tree.item(n, "values")[0] for n in selected_nodes]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(keys)} object(s)?")
        if not confirm:
            return

        total = len(keys)
        completed = 0

        for k in keys:
            self.s3.delete_objects([k])
            completed += 1
            self.update_progress(completed, total)
            self.logger.log(f"Deleted: s3://{self.s3.bucket}/{k}")

        self.logger.log(f"Deletion complete: {completed}/{total} object(s).")
        self.reset_progress()
        self.refresh_s3_tree()

    def create_s3_folder(self):
        folder_name = simpledialog.askstring("Folder Name", "Enter new folder name:")
        if not folder_name:
            return
        if not folder_name.endswith("/"):
            folder_name += "/"
        self.s3.create_folder(folder_name)
        self.logger.log(f"Created S3 folder: {folder_name}")
        self.refresh_s3_tree()

    def view_object_url(self):
        selected_nodes = self.s3_tree.selection()
        if not selected_nodes:
            messagebox.showwarning("Select File", "Select a single object to view.")
            return
        key = self.s3_tree.item(selected_nodes[0], "values")[0]
        url = self.s3.get_object_url(key)
        webbrowser.open(url)
        self.logger.log(f"Opened URL: {url}")

    def refresh_s3_tree(self):
        self.s3_tree.delete(*self.s3_tree.get_children())
        self.populate_s3_root()


# Updated execution block
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cloud File Manager (Standalone)")
    root.geometry("1300x950")
    # Dock the frame to the root window for standalone use
    app = CloudManagerApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()