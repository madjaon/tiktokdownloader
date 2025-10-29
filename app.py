import os
import re
import yt_dlp
import sys
import win32com.client
import pyperclip
from datetime import datetime

# pyinstaller --onefile --icon=icon.ico --hidden-import=win32com --hidden-import=win32com.shell app.py
def create_shortcut():
    """Tự động tạo shortcut TikTok Downloader trên Desktop."""
    try:
        from win32com.shell import shell, shellcon # type: ignore
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)

        shortcut_path = os.path.join(desktop, "TikTok Downloader.lnk")

        # ✅ Xác định đúng đường dẫn đang chạy (dù là .py hay .exe)
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable  # Khi chạy file .exe (PyInstaller)
        else:
            exe_path = os.path.abspath(__file__)  # Khi chạy file .py

        if not os.path.exists(shortcut_path):
            shell_obj = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell_obj.CreateShortcut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.IconLocation = os.path.join(os.path.dirname(exe_path), "icon.ico")
            shortcut.Save()
            print(f"🎯 Đã tạo shortcut trên Desktop: {shortcut_path}\n")
        else:
            print("✅ Shortcut đã tồn tại.")
    except Exception as e:
        print(f"⚠️ Không thể tạo shortcut: {e}")


def get_tiktok_url():
    """Tự động lấy link TikTok từ clipboard, nếu không có thì yêu cầu nhập tay."""
    clipboard = pyperclip.paste().strip()

    # Kiểm tra xem clipboard có chứa link TikTok không
    if re.match(r"^https?://(www\.)?tiktok\.com/", clipboard):
        print(f"📋 Đã phát hiện link TikTok trong clipboard:\n👉 {clipboard}\n")
        use_clipboard = input("Dùng link này? (Y/n): ").strip().lower()
        if use_clipboard in ("", "y", "yes"):
            return clipboard

    # Nếu không có hoặc người dùng chọn nhập tay
    return input("Nhập đường dẫn TikTok (kênh hoặc playlist): ").strip()


def log_error_if_failed(d, error_log):
    """Ghi log nếu video bị lỗi tải."""
    if d.get("status") == "error":
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] ERROR: {d.get('filename', 'unknown file')}\n")


def download_tiktok_videos(url):
    base_dir = os.path.join(os.path.expanduser("~"), "Downloads", "tiktok")

    # ✅ Lấy tên kênh TikTok (sau dấu "@")
    username_match = re.search(r"tiktok\.com/@([\w\.-]+)", url)
    username = username_match.group(1) if username_match else "unknown_user"

    # ✅ Kiểm tra nếu là playlist
    playlist_match = re.search(r"/playlist/([^/?#]+)", url)
    if playlist_match:
        playlist_name = playlist_match.group(1)
        save_path = os.path.join(base_dir, username, playlist_name)
    else:
        save_path = os.path.join(base_dir, username)

    os.makedirs(save_path, exist_ok=True)

    # ✅ File lưu ID các video đã tải
    archive_file = os.path.join(save_path, "downloaded.txt")
    # ✅ File lưu log lỗi
    error_log = os.path.join(save_path, "errors.log")

    # ✅ Cấu hình yt-dlp
    ydl_opts = {
        "outtmpl": os.path.join(save_path, "%(id)s.%(ext)s"),  # tên file chỉ gồm ID
        "format": "mp4",
        "retries": 15,                   # retry tối đa 15 lần nếu lỗi mạng
        "fragment_retries": 15,          # retry từng mảnh video
        "skip_unavailable_fragments": True,
        "ignoreerrors": True,            # bỏ qua video lỗi
        "nopart": True,                  # không lưu file tạm .part
        "quiet": False,
        "noplaylist": False,
        "merge_output_format": "mp4",
        "download_archive": archive_file,  # bỏ qua video đã tải (theo ID)
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
        ],
        # ✅ Giúp TikTok tránh lỗi impersonation
        "extractor_args": {"tiktok": {"use_har_extractor": ["true"]}},
        # ✅ Ghi log lỗi nếu video lỗi
        "progress_hooks": [
            lambda d: log_error_if_failed(d, error_log)
        ],
    }

    print(f"\n🚀 Đang tải video từ: {url}")
    print(f"💾 Lưu vào: {save_path}")
    print("📋 Bỏ qua các video đã tải (theo ID).\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"\n📘 Danh sách ID video đã tải: {archive_file}")
    print(f"⚠️  Nếu có lỗi, xem file log: {error_log}\n")


if __name__ == "__main__":
    print("=== 🧠 TikTok Downloader Auto Tool ===")

    try:
        create_shortcut()
        url = get_tiktok_url()
        if not url:
            print("⚠️ Không có đường dẫn TikTok hợp lệ. Thoát...")
        else:
            download_tiktok_videos(url)

    except Exception as e:
        print(f"❌ Lỗi: {e}")

    print("\n✅ Hoàn tất! Kiểm tra thư mục Downloads/tiktok.\n")
    os.system("pause")  # Dừng lại, chờ nhấn phím bất kỳ
