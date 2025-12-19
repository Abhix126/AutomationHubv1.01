\# 🛸 Automation Hub v1.0



\[!\[Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)





\*\*Automation Hub\*\* is a modular, plug-and-play desktop suite that centralizes Cloud Management, Git Webhooks, and OCR utilities in a single developer-friendly interface.  



Unlike traditional apps, Automation Hub uses a \*\*Virtual Viewport system\*\*, keeping tools alive with active threads, terminal logs, and background states.



---



\## 🌌 Features



\### Triple-Threat Toolkit

| Feature           | Technology     | Use Case |

|------------------|---------------|---------|

| \*\*Cloud Manager\*\* | `boto3`       | Bridge local storage with AWS S3 buckets seamlessly. |

| \*\*Git Notifier\*\*  | `cloudflared` | Receive always-on-top desktop alerts for Git events. |

| \*\*OCR Utility\*\*   | `Tesseract`   | Convert clipboard images into editable text instantly. |



\### Key Graphical Enhancements

\- \*\*State-Persistent Sidebar:\*\* Navigate between tasks without killing them. Active features highlighted in blue.  

\- \*\*System-Modal Alerts:\*\* Windows-level notifications (priority 4096) float above all apps.  

\- \*\*Green-on-Black Consoles:\*\* Real-time terminal output for a “Developer Command Center” vibe.  



---



\## 🏗 Architecture



The Hub uses \*\*Namespace Isolation\*\*, where each module lives in its own folder, preventing dependency conflicts.



```mermaid

graph LR

&nbsp;   A\[Main Hub] --> B(Cloud Manager)

&nbsp;   A --> C(GitHub Notifier)

&nbsp;   A --> D(OCR Utility)

&nbsp;   style A fill:#4a69bd,stroke:#333,stroke-width:2px

⚙️ Installation

1\. Prerequisites

Ensure the following are in your system PATH:



Tesseract OCR Engine



Cloudflared CLI



2\. Python Dependencies

bash

Copy code

pip install boto3 pytesseract pyperclip requests flask psutil pillow

3\. Folder Structure

bash

Copy code

.

├── main\_hub.py

├── Cloud\_File\_Manager/

├── Github\_Notifier/

└── OCR\_Clipboard\_Utility/

🚀 Usage

Run the main controller to start the Hub:



bash

Copy code

python main\_hub.py

📜 Development Notes

Lazy Loading: Modules initialize only when accessed, saving resources.



Path Injection: Dynamically adds subfolders to sys.path, allowing isolated cred.py files without conflicts.





💡 Contributing

Contributions are welcome! Please open issues or submit pull requests.





