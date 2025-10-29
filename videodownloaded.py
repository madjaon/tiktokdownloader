import os
import re

# 🔧 Thư mục chứa các file TikTok
folder_path = r"C:\Users\Administrator\Downloads\tiktok\channel"

# 🔧 Tên file kết quả
output_file = os.path.join(folder_path, "downloaded.txt")

# ✅ Lấy danh sách tất cả file trong thư mục
files = os.listdir(folder_path)

# ✅ Lọc và xử lý
results = []

for filename in files:
    # Ví dụ: 1112223334445556667.mp4
    match = re.match(r"(\d+)\.mp4", filename)
    if match:
        video_id = match.group(1)
        results.append(f"tiktok {video_id}")

# ✅ Ghi ra file downloaded.txt
with open(output_file, "w", encoding="utf-8") as f:
    for line in results:
        f.write(line + "\n")

print(f"✅ Đã ghi {len(results)} dòng vào: {output_file}")
