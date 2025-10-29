import os
import re

# 📁 Thư mục chứa các file
folder = r"C:\Users\Administrator\Downloads\tiktok\channel"

# 🔁 Duyệt qua toàn bộ file trong thư mục
for filename in os.listdir(folder):
    old_path = os.path.join(folder, filename)

    # Bỏ qua nếu không phải là file
    if not os.path.isfile(old_path):
        continue

    # 🔍 Tìm các file có dạng "tiktok_<số>.mp4"
    match = re.match(r"tiktok_(\d+)\.mp4$", filename)
    if match:
        new_name = match.group(1) + ".mp4"
        new_path = os.path.join(folder, new_name)

        # ⚡ Đổi tên file
        os.rename(old_path, new_path)
        print(f"✅ Đã đổi: {filename} → {new_name}")

print("🎉 Hoàn tất đổi tên tất cả file!")
