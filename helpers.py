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

# خادم الويب لإبقاء السيرفر نشطاً 24/7
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Imperial Bot Engine is fully secure and online 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def auto_clean_temp_files():
    """تنظيف تلقائي دوري للذاكرة المؤقتة كل 10 دقائق"""
    while True:
        time.sleep(600)
        try:
            for f in glob.glob("downloads/*"):
                if os.path.isfile(f):
                    os.remove(f)
        except Exception:
            pass

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
        logging.error(f"Error saving users data: {e}")

def track_user(user, phone_number=None):
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
            "phone": phone_number or "غير متوفر",
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
        if phone_number: users[uid]["phone"] = phone_number

    save_users(users)

def extract_url(text: str) -> str:
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(0).split('?')[0] if match else ""

def is_content_safe(text: str) -> bool:
    """فلترة أمنية لمنع سحب أو تمرير أي محتوى إباحي أو احتيالي خبيث"""
    forbidden = [
        "porn", "xxx", "sex", "nude", "adult", "18+", "pantera", "kazpantera",
        "اباحي", "جنس", "سكس", "تعري", "مؤخرة", "شذوذ", "فضيحة"
    ]
    txt_low = text.lower()
    return not any(w in txt_low for w in forbidden)

def trim_video_to_size(input_path: str, output_path: str, target_size=MAX_SAFE_BYTES) -> bool:
    try:
        if os.path.getsize(input_path) <= target_size:
            return False
        cmd_dur = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path
        ]
        res = subprocess.run(cmd_dur, stdout=subprocess.PIPE, text=True)
        dur = float(res.stdout.strip()) if res.stdout.strip() else 240.0
        trim_sec = max(10, math.floor(dur * ((target_size * 0.92) / os.path.getsize(input_path))))

        cmd = ["ffmpeg", "-y", "-i", input_path, "-t", str(trim_sec), "-c", "copy", output_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception:
        return False

def download_tiktok_smart(url: str, output_path: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        api = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("hdplay") or res["data"].get("play") or res["data"].get("wmplay")
            if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
            with open(output_path, "wb") as f:
                f.write(requests.get(dl_url, headers=headers, timeout=40).content)
            return {"title": res["data"].get("title", "تيك توك بدون علامة مائية"), "path": output_path}
    except Exception:
        pass

    try:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_path,
            "quiet": True,
            "nocheckcertificate": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"title": info.get("title", "مقطع تيك توك"), "path": output_path}
    except Exception:
        return None

def search_and_download_audio_robust(query: str, output_base: str):
    """محرك بحث صوتي متدرج لجلب الشيلات والأغاني بصيغة MP3 نقي 320kbps"""
    clean_q = re.sub(r'^(اريد|اعطني|تنزيل|تحميل|شيله|شيلة|اغنيه|اغنية|صوت|زامل)\s*', '', query).strip()
    search_queries = [
        f"ytsearch1:{query}",
        f"ytsearch1:{clean_q} شيلة كاملة mp3",
        f"ytsearch1:{clean_q} mp3 audio",
        f"scsearch1:{clean_q}"
    ]

    opts = {
        "outtmpl": f"{output_base}.%(ext)s",
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320"
        }],
    }

    for sq in search_queries:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(sq, download=True)
                title = "شيلة صوتية كاملة"
                if "entries" in info and len(info["entries"]) > 0:
                    title = info["entries"][0].get("title", clean_q)
                elif "title" in info:
                    title = info.get("title", clean_q)

                for f in glob.glob(f"{output_base}*"):
                    if os.path.exists(f) and os.path.getsize(f) > 5000:
                        return {"path": f, "title": title}
        except Exception:
            continue

    return None

def download_universal_media(target: str, output_path: str, is_search=False):
    query = f"ytsearch1:{target}" if is_search else target
    opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
        "merge_output_format": "mp4"
    }
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
    return f"طلبك بخصوص <b>{prompt}</b> تحت أمرك دائماً وبأعلى جودة يا غالي 🌸✨"
