import os
import re
import yt_dlp
from datetime import datetime

# Build exe
# pip install pyinstaller
# pyinstaller --onefile app.py
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
        "extractor_args": {"tiktok": {"use_har_extractor": ["true"]}},  # giả trình duyệt
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


def log_error_if_failed(d, error_log):
    """Ghi log nếu video bị lỗi tải."""
    if d.get('status') == 'error':
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] ERROR: {d.get('filename', 'unknown file')}\n")


if __name__ == "__main__":
    print("=== 🧠 TikTok Downloader Auto Tool ===")
    url = input("Nhập đường dẫn TikTok (kênh hoặc playlist): ").strip()
    download_tiktok_videos(url)
    print("\n✅ Hoàn tất! Kiểm tra thư mục Downloads/tiktok.\n")

    # ✅ Chờ người dùng nhấn phím trước khi thoát
    input("👉 Nhấn Enter để thoát...")
