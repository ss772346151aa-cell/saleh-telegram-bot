import os
import glob
import logging
import threading
import time
import json
import re
import math
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import yt_dlp

MAX_SAFE_BYTES = 48 * 1024 * 1024
USERS_FILE = "bot_users.json"

# خادم الويب للحفاظ على سيرفر Render يقظاً 24/7
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is online 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def auto_clean_temp_files():
    while True:
        time.sleep(600)
        try:
            for f in glob.glob("downloads/*"):
                if os.path.isfile(f):
                    os.remove(f)
        except Exception:
            pass

# إدارة بيانات الزوار بدقة كاملة
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving users: {e}")

def track_user(user):
    """سحب كل معلومة متاحة عن الزائر من تيليجرام وتخزينها"""
    if not user:
        return
    users = load_users()
    uid = str(user.id)
    now_time = time.strftime("%Y-%m-%d %H:%M:%S")

    if uid not in users:
        users[uid] = {
            "id": user.id,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": f"@{user.username}" if user.username else "بدون يوزر",
            "language_code": user.language_code or "غير محدد",
            "is_premium": getattr(user, "is_premium", False),
            "first_join": now_time,
            "last_active": now_time,
            "interactions": 1
        }
    else:
        users[uid]["last_active"] = now_time
        users[uid]["interactions"] = users[uid].get("interactions", 0) + 1
        if user.first_name: users[uid]["first_name"] = user.first_name
        if user.last_name: users[uid]["last_name"] = user.last_name
        if user.username: users[uid]["username"] = f"@{user.username}"

    save_users(users)

def extract_url(text: str) -> str:
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(0).split('?')[0] if match else ""

def trim_video_to_size(input_path: str, output_path: str, target_size=MAX_SAFE_BYTES) -> bool:
    try:
        if os.path.getsize(input_path) <= target_size:
            return False
        cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
        res = subprocess.run(cmd_dur, stdout=subprocess.PIPE, text=True)
        dur = float(res.stdout.strip()) if res.stdout.strip() else 240.0
        trim_sec = max(10, math.floor(dur * ((target_size * 0.92) / os.path.getsize(input_path))))

        cmd = ["ffmpeg", "-y", "-i", input_path, "-t", str(trim_sec), "-c", "copy", output_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception:
        return False

def download_tiktok_smart(url: str, output_path: str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        api = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("hdplay") or res["data"].get("play") or res["data"].get("wmplay")
            if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
            with open(output_path, "wb") as f:
                f.write(requests.get(dl_url, headers=headers, timeout=40).content)
            return {"title": res["data"].get("title", "تيك توك"), "path": output_path}
    except Exception:
        pass
    try:
        with yt_dlp.YoutubeDL({"format": "bestvideo+bestaudio/best", "outtmpl": output_path, "quiet": True}) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"title": info.get("title", "تيك توك"), "path": output_path}
    except Exception:
        return None

def download_universal_media(target: str, output_path: str, is_audio=False, is_search=False):
    query = f"ytsearch1:{target}" if is_search else target
    opts = {
        "outtmpl": output_path,
        "quiet": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    if is_audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]
    else:
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=True)
        return info["entries"][0] if "entries" in info and len(info["entries"]) > 0 else info

def ask_super_ai(prompt: str) -> str:
    try:
        sys_p = "أنت المساعد الذكي الخارق لصلوح المانعي. قدم إجابات وافية وممتعة باللغة العربية مع إيموجي."
        url = "https://text.pollinations.ai/" + urllib.parse.quote(f"{sys_p}\nالسؤال: {prompt}")
        res = requests.get(url, timeout=6)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass
    return f"طلبك بخصوص {prompt} تحت أمرك دائماً يا غالي 🌸✨"
