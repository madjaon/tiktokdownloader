import os
import re
import sys
import threading
import yt_dlp
import pyperclip
import win32com.client
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

# pyinstaller --noconsole --onefile --icon=icon.ico --hidden-import=win32com --hidden-import=win32com.shell app_gui.py

# === Hàm tạo shortcut trên Desktop ===
def create_shortcut():
    try:
        from win32com.shell import shell, shellcon # type: ignore
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
        shortcut_path = os.path.join(desktop, "TikTok Downloader.lnk")

        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)

        if not os.path.exists(shortcut_path):
            shell_obj = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell_obj.CreateShortcut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.IconLocation = os.path.join(os.path.dirname(exe_path), "icon.ico")
            shortcut.Save()
    except Exception as e:
        print("⚠️ Không thể tạo shortcut:", e)


# === Hàm lấy link TikTok từ clipboard ===
def get_tiktok_url():
    clipboard = pyperclip.paste().strip()
    if re.match(r"^https?://(www\.)?tiktok\.com/", clipboard):
        return clipboard
    return ""


# === Lớp GUI chính ===
class TikTokDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 TikTok Downloader")
        self.geometry("600x800")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.downloading = False
        self.download_thread = None

        # --- Giao diện chính ---
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.label = ctk.CTkLabel(
            self,
            text="🎬 TikTok Downloader - Tải video nhanh chóng\n",
            font=("Segoe UI", 18, "bold"), # Arial
            text_color="#0066cc",
        )
        self.label.pack(pady=10)

        # ✅ Ghi chú cho người dùng phổ thông
        self.note_label = ctk.CTkLabel(
            self,
            text=(
                "💡 Bạn có thể nhập:\n"
                "• Link video TikTok để tải 1 video duy nhất\n"
                "• Hoặc link kênh (@tên) để tải tất cả video của kênh đó\n"
                "• Hoặc link playlist để tải toàn bộ danh sách\n"
            ),
            font=("Arial", 14),
        )
        self.note_label.pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, width=500, placeholder_text="https://www.tiktok.com/@username/video/...")
        self.url_entry.pack(pady=10)

        self.clipboard_btn = ctk.CTkButton(self, text="📋 Dán từ Clipboard", command=self.paste_from_clipboard)
        self.clipboard_btn.pack(pady=5)

        self.start_btn = ctk.CTkButton(self, text="🚀 Bắt đầu tải", command=self.start_download)
        self.start_btn.pack(pady=15)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=10)

        self.status_text = tk.StringVar(value="Chờ lệnh tải...")
        self.status_label = ctk.CTkLabel(self, textvariable=self.status_text, font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.log_box = tk.Text(self, height=8, wrap="word", bg="#1e1e1e", fg="#dcdcdc")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.exit_btn = ctk.CTkButton(self, text="❌ Thoát", fg_color="red", hover_color="#b30000", command=self.on_close)
        self.exit_btn.pack(pady=10)

        create_shortcut()

    def paste_from_clipboard(self):
        url = get_tiktok_url()
        if url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            # messagebox.showinfo("Clipboard", f"Đã dán link TikTok:\n{url}")
        else:
            messagebox.showwarning("Clipboard", "Không phát hiện link TikTok trong clipboard.")

    def log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.update_idletasks()

    def start_download(self):
        if self.downloading:
            messagebox.showinfo("Đang tải", "Quá trình tải đang diễn ra.")
            return

        url = self.url_entry.get().strip()
        if not url:
            url = get_tiktok_url()
        if not url:
            messagebox.showerror("Lỗi", "Không có đường dẫn TikTok hợp lệ.")
            return

        self.status_text.set("🔄 Đang tải video...")
        self.progress.set(0)
        self.log(f"=== Bắt đầu tải: {url} ===")

        self.downloading = True
        self.download_thread = threading.Thread(target=self.download_tiktok_videos, args=(url,))
        self.download_thread.start()

    def download_tiktok_videos(self, url):
        base_dir = os.path.join(os.path.expanduser("~"), "Downloads", "tiktok")
        username_match = re.search(r"tiktok\.com/@([\w\.-]+)", url)
        username = username_match.group(1) if username_match else "unknown_user"
        save_path = os.path.join(base_dir, username)
        os.makedirs(save_path, exist_ok=True)

        archive_file = os.path.join(save_path, "downloaded.txt")
        error_log = os.path.join(save_path, "errors.log")

        ydl_opts = {
            "outtmpl": os.path.join(save_path, "%(id)s.%(ext)s"),
            "format": "mp4",
            "retries": 10,
            "fragment_retries": 10,
            "skip_unavailable_fragments": True,
            "ignoreerrors": True,
            "noplaylist": False,
            "download_archive": archive_file,
            "quiet": True,
            "progress_hooks": [self.hook_progress],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.status_text.set("✅ Tải hoàn tất!")
            self.log("✅ Tải xong! Kiểm tra thư mục Downloads/tiktok/")
        except Exception as e:
            self.status_text.set("❌ Lỗi khi tải!")
            self.log(f"Lỗi: {e}")
        finally:
            self.downloading = False

    def hook_progress(self, d):
        if d["status"] == "downloading":
            try:
                percent = d.get("_percent_str", "0%").replace("%", "").strip()
                self.progress.set(float(percent) / 100)
                self.status_text.set(f"Đang tải: {percent}%")
            except Exception:
                pass
        elif d["status"] == "finished":
            self.status_text.set("Hoàn tất 1 video!")
            self.progress.set(1)

    def on_close(self):
        if self.downloading:
            if not messagebox.askyesno("Thoát", "Đang tải video. Bạn có chắc muốn dừng không?"):
                return
        self.destroy()


if __name__ == "__main__":
    app = TikTokDownloaderApp()
    app.mainloop()
