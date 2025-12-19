import datetime
import threading

class AppLogger:
    def __init__(self, text_widget=None, log_file="logs.txt"):
        self.text_widget = text_widget
        self.log_file = log_file
        self.lock = threading.Lock()

        # Initialize log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n--- Application Started: {datetime.datetime.now()} ---\n")

    def log(self, message):
        """Logs a message with timestamp to GUI and file."""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        line = f"{timestamp} {message}"

        # Write to file
        with self.lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        # Write to GUI
        if self.text_widget:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", line + "\n")
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
