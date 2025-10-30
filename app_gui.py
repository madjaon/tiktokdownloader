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
import subprocess

# =========================
# ⚙️ Lệnh đóng gói EXE:
# pyinstaller --noconsole --onefile --icon=icon.ico --hidden-import=win32com --hidden-import=win32com.shell app_gui.py
# =========================


# === Hàm tạo shortcut trên Desktop ===
def create_shortcut():
    """Tự động tạo shortcut trên Desktop nếu chưa có"""
    try:
        from win32com.shell import shell, shellcon  # type: ignore
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
        shortcut_path = os.path.join(desktop, "Video Downloader.lnk")

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


# === Hàm lấy link video từ clipboard ===
def get_video_url():
    """Tự động lấy link hợp lệ từ clipboard (TikTok, YouTube, Facebook...)"""
    clipboard = pyperclip.paste().strip()
    if re.match(r"^https?://", clipboard):
        return clipboard
    return ""


# === Lớp GUI chính ===
class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Video Downloader")
        self.geometry("600x620")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.downloading = False
        self.download_thread = None
        self.stop_flag = False
        self.current_save_path = None

        # --- Giao diện chính ---
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.label = ctk.CTkLabel(
            self,
            text="🎬 Video Downloader",
            font=("Segoe UI", 18, "bold"),
            text_color="#0066cc",
        )
        self.label.pack(pady=10)

        # ✅ Ghi chú rõ ràng cho người dùng phổ thông
        self.note_label = ctk.CTkLabel(
            self,
            text=(
                "💡 Bạn có thể nhập link từ các nguồn sau:\n"
                "• YouTube: video, playlist hoặc kênh\n"
                "• TikTok: video, playlist hoặc toàn bộ kênh\n"
                "• Facebook, Instagram, Twitter, v.v...\n\n"
                "👉 Hệ thống sẽ tự nhận dạng và tải video phù hợp.\n"
                "👉 Có thể dán link 1 video đơn lẻ hoặc link danh sách.\n"
                "👉 Video sẽ được lưu vào thư mục riêng: \nDownloads/videos/tiktok/ hoặc Downloads/videos/youtube/"
            ),
            font=("Arial", 14),
            justify="left",
        )
        self.note_label.pack(pady=10)

        self.url_entry = ctk.CTkEntry(
            self, width=500, placeholder_text="Dán link video tại đây..."
        )
        self.url_entry.pack(pady=10)

        self.clipboard_btn = ctk.CTkButton(
            self, text="📋 Dán từ Clipboard", command=self.paste_from_clipboard
        )
        self.clipboard_btn.pack(pady=5)

        self.start_btn = ctk.CTkButton(
            self, text="🚀 Bắt đầu tải", command=self.start_download
        )
        self.start_btn.pack(pady=15)

        # ⚙️ Nút mở thư mục tải (ẩn mặc định)
        self.open_folder_btn = ctk.CTkButton(
            self,
            text="📂 Mở thư mục tải về",
            command=self.open_download_folder,
        )
        self.open_folder_btn.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=10)

        self.status_text = tk.StringVar(value="Chờ lệnh tải...")
        self.status_label = ctk.CTkLabel(
            self, textvariable=self.status_text, font=("Arial", 12)
        )
        self.status_label.pack(pady=10)

        self.log_box = tk.Text(
            self,
            height=4,
            wrap="word",
            bg="#1e1e1e",
            fg="#dcdcdc",
            state="disabled",  # 🚫 chặn nhập từ người dùng
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.exit_btn = ctk.CTkButton(
            self,
            text="❌ Thoát",
            fg_color="red",
            hover_color="#b30000",
            command=self.on_close,
        )
        self.exit_btn.pack(pady=10)

        create_shortcut()

    # === Các hàm xử lý GUI ===
    def paste_from_clipboard(self):
        """Dán link từ clipboard"""
        url = get_video_url()
        if url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        else:
            messagebox.showwarning("Clipboard", "Không phát hiện link hợp lệ trong clipboard.")

    def log(self, message):
        self.log_box.configure(state="normal")  # bật tạm để ghi
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")  # khóa lại
        self.update_idletasks()

    def disable_inputs(self):
        """Vô hiệu hóa các nút nhập khi đang tải"""
        self.url_entry.configure(state="disabled")
        self.clipboard_btn.configure(state="disabled")
        self.start_btn.configure(state="disabled")

    def enable_inputs(self):
        """Kích hoạt lại các nút nhập sau khi tải xong"""
        self.url_entry.configure(state="normal")
        self.clipboard_btn.configure(state="normal")
        self.start_btn.configure(state="normal")

    def start_download(self):
        """Bắt đầu tải video"""
        if self.downloading:
            messagebox.showinfo("Đang tải", "Quá trình tải đang diễn ra.")
            return

        url = self.url_entry.get().strip()
        if not url:
            url = get_video_url()
        if not url:
            messagebox.showerror("Lỗi", "Vui lòng nhập hoặc dán một đường dẫn video hợp lệ.")
            return

        self.status_text.set("🔄 Đang tải video...")
        self.progress.set(0)
        self.log(f"=== Bắt đầu tải: {url} ===")

        # Ẩn input và nút (main thread)
        self.disable_inputs()

        # Hiện nút mở thư mục
        self.open_folder_btn.pack(pady=5)

        self.downloading = True
        self.download_thread = threading.Thread(
            target=self.download_videos, args=(url,)
        )
        self.download_thread.start()

    # === Tải video bằng yt_dlp ===
    def download_videos(self, url):
        base_dir = os.path.join(os.path.expanduser("~"), "Downloads", "videos")

        # 🔎 Xác định nền tảng (TikTok, YouTube, Facebook, Instagram...)
        platform = "others"
        url_lower = url.lower()

        if "tiktok" in url_lower:
            platform = "tiktok"
        elif "youtube" in url_lower or "youtu.be" in url_lower:
            platform = "youtube"
        elif "facebook" in url_lower or "fb.watch" in url_lower:
            platform = "facebook"
        elif "instagram" in url_lower:
            platform = "instagram"
        elif "twitter" in url_lower or "x.com" in url_lower:
            platform = "twitter"
        elif "bilibili" in url_lower:
            platform = "bilibili"
        elif "vimeo" in url_lower:
            platform = "vimeo"
        elif "viki" in url_lower or "vikichannel" in url_lower:
            platform = "vikichannel"

        # 📁 Tạo thư mục lưu theo từng nền tảng
        save_path = os.path.join(base_dir, platform)
        os.makedirs(save_path, exist_ok=True)
        self.current_save_path = save_path

        # 🧾 Lưu danh sách ID đã tải để bỏ qua trùng lặp
        archive_file = os.path.join(save_path, "downloaded.txt")

        # 🎯 Nếu là TikTok → dùng ID làm tên file
        if platform == "tiktok":
            filename_template = "%(id)s.%(ext)s"
        else:
            filename_template = "%(title)s.%(ext)s"

        # ⚙️ Cấu hình yt-dlp
        ydl_opts = {
            "outtmpl": os.path.join(save_path, filename_template),
            "format": "mp4",
            "merge_output_format": "mp4",
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
            self.log(f"🚀 Bắt đầu tải từ nền tảng: {platform}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self.stop_flag:
                    ydl.download([url])

            self.status_text.set("✅ Tải hoàn tất!")
            self.log(f"✅ Tải xong! Kiểm tra thư mục: {save_path}")

        except Exception as e:
            self.status_text.set("❌ Lỗi khi tải!")
            self.log(f"Lỗi: {e}")

        finally:
            # Schedule showing inputs back on the main/UI thread
            try:
                self.after(0, self.enable_inputs)
            except Exception:
                pass
            self.downloading = False

    def open_download_folder(self):
        """Mở thư mục chứa video tải về"""
        if self.current_save_path and os.path.exists(self.current_save_path):
            subprocess.run(["explorer", self.current_save_path])
        else:
            messagebox.showinfo("Thư mục", "Chưa có thư mục tải nào được tạo.")

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
        """Đảm bảo thoát hoàn toàn khi đóng cửa sổ hoặc ấn nút Thoát"""
        if self.downloading:
            if not messagebox.askyesno(
                "Thoát", "Đang tải video. Bạn có chắc muốn dừng và thoát không?"
            ):
                return
            self.stop_flag = True  # Đánh dấu dừng tải

        try:
            # Đóng hoàn toàn GUI
            self.destroy()

            # Nếu còn thread đang chạy → chờ kết thúc nhẹ nhàng
            if self.download_thread and self.download_thread.is_alive():
                self.download_thread.join(timeout=2)
        except Exception:
            pass

        # Thoát hoàn toàn process (kể cả thread còn sót)
        os._exit(0)

# === Chạy chương trình chính ===
if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
