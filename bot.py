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
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

# ==================== الإعدادات وهوية البوت الإمبراطوري ====================
BOT_TOKEN = "9157081412:AAF-LegdEK1zKi_ZUCPOarhFXwphmPpqFUE"
BOT_NAME = "بوت صلوح المانعي الذكي ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
CHANNEL_URL = "https://t.me/saleh_down_bot"
MAX_SAFE_BYTES = 48 * 1024 * 1024  # سقف الأمان للإرسال عبر تيليجرام (48MB)
USERS_FILE = "bot_users.json"
ADMIN_ID = 0  # استبدل 0 بآيدي حسابك الشخصي (احصل عليه من @userinfobot)
# =========================================================================

# 1. خادم الويب للحفاظ على نشاط Render 24/7
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is online and running 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def auto_clean_temp_files():
    """تنظيف الملفات المؤقتة دورياً للحفاظ على الذاكرة وسرعة السيرفر"""
    while True:
        time.sleep(600)
        try:
            for f in glob.glob("downloads/*"):
                if os.path.isfile(f):
                    os.remove(f)
        except Exception:
            pass

# 2. نظام تتبع وإحصائيات الزوار والمستخدمين
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users_data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving users: {e}")

def track_user(user):
    if not user:
        return
    users = load_users()
    uid = str(user.id)
    today = time.strftime("%Y-%m-%d")
    
    if uid not in users:
        users[uid] = {
            "first_name": user.first_name,
            "username": user.username or "None",
            "joined_date": today,
            "last_active": today,
            "interactions": 1
        }
    else:
        users[uid]["last_active"] = today
        users[uid]["interactions"] = users[uid].get("interactions", 0) + 1

    save_users(users)

def extract_url(text: str) -> str:
    pattern = r'(https?://[^\s]+)'
    match = re.search(pattern, text)
    if match:
        return match.group(0).split('?')[0]
    return ""

def get_video_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def trim_video_to_size(input_path: str, output_path: str, target_size_bytes=MAX_SAFE_BYTES) -> bool:
    try:
        current_size = os.path.getsize(input_path)
        if current_size <= target_size_bytes:
            return False

        duration = get_video_duration(input_path)
        trim_seconds = 240 if duration <= 0 else max(10, math.floor(duration * ((target_size_bytes * 0.92) / current_size)))

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-t", str(trim_seconds),
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        logging.error(f"Error trimming video: {e}")
        return False

def download_tiktok_smart(url: str, output_path: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api_url, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("hdplay") or res["data"].get("play") or res["data"].get("wmplay")
            title = res["data"].get("title", "مقطع تيك توك حصري")
            if dl_url.startswith("/"):
                dl_url = "https://www.tikwm.com" + dl_url
            v_data = requests.get(dl_url, headers=headers, timeout=40).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path}
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
        pass

    return None

def download_universal_media(target: str, output_path: str, is_audio=False, is_search=False):
    query = f"ytsearch1:{target}" if is_search else target
    ydl_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if is_audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]
    else:
        ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"
        ydl_opts["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def ask_super_ai(prompt: str) -> str:
    p = prompt.lower().strip()
    if any(w in p for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي! نورتني وأسعدتني بوجودك 🌹👑\n\n"
            f"أنا المساعد الذكي الخارق لـ <b>صلوح المانعي</b>.\n"
            f"تابع حسابنا المعتمد على تيك توك: <b>{TIKTOK_USER}</b>\n\n"
            "✨ اطلب أي شيلة، فيلم، مباراة، أو رابط تيك توك، وسأقوم بسحبه لك فوراً!"
        )

    try:
        sys_prompt = "أنت المساعد الذكي الخارق والمطور لصلوح المانعي. أجب باحترافية وتفصيل مع إيموجي باللغة العربية دون عجز."
        url = "https://text.pollinations.ai/" + urllib.parse.quote(f"{sys_prompt}\nالسؤال: {prompt}")
        res = requests.get(url, timeout=6)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> على راسي من فوق! أعمل على تلبية طلبك بأعلى جودة تليق بك دائماً 🌸✨"

# ==================== دليل الاستخدام والأوامر ====================

def get_help_message():
    return (
        "📖 <b>دليل الاستخدام السريع والسهل — خطوة بخطوة:</b> 🚀\n\n"
        "✨ <i>أهلاً بك يا غالي! البوت مصمم ليخدمك في ثوانٍ بدون أي تعقيد:</i>\n\n"
        "1️⃣ <b>تنزيل تيك توك بدون علامة مائية:</b>\n"
        "• ادخل التيك توك واضغط على زر (مشاركة ↗️) ثم (نسخ الرابط 📋).\n"
        "• الصق الرابط هنا في البوت، وسيصلك الفيديو فوراً وبأعلى دقة!\n\n"
        "2️⃣ <b>تحميل الشيلات والأغاني صوت MP3 فوراً:</b>\n"
        "• فقط اكتب اسم الشيلة أو الأغنية مباشرة (مثال: <code>شيلة فهد بن فصلا</code> أو <code>اغنية كذا</code>).\n"
        "• سيقوم البوت باستخراج ملف الصوت فوراً ليعمل في مشغل تيليجرام بنقاوة عالية.\n\n"
        "3️⃣ <b>الأفلام والملخصات والمباريات:</b>\n"
        "• اكتب اسم أي فيلم أو مباراة (مثال: <code>فيلم اكشن 2024</code> أو <code>اهداف الكلاسيكو</code>).\n"
        "• سيقوم البوت بسحب أفضل مقطع وملخص متوفر، مع ميزة القص التلقائي إذا كان الحجم كبيراً!\n\n"
        "4️⃣ <b>الدردشة والذكاء الاصطناعي:</b>\n"
        "• اسأل البوت عن أي معلومة، مسألة، أو استشارة وسيجيبك بذكاء خارق.\n\n"
        "👇 <b>جرب الآن: أرسل أي رابط أو اكتب طلبك مباشرة وسيبهرك البوت!</b>"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>أقوى وأسهل بوت وسائط وذكاء اصطناعي على الإطلاق!</b>\n\n"
        "🔥 <b>ماذا يمكن للبوت أن يقدم لك؟</b>\n"
        "• 📥 <b>سحب تيك توك:</b> بدون علامة مائية وبأعلى دقة (HD).\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> استخراج صوتي نقي 320kbps فوراً.\n"
        "• 🎬 <b>أفلام ومباريات:</b> مقاطع وملخصات مع قص ذكي للأحجام الكبيرة.\n"
        "• 🧠 <b>ذكاء اصطناعي شامل:</b> إجابات وتحليلات فورية بدون عجز.\n\n"
        f"🌟 <b>حسابنا الرسمي على تيك توك لمشاهدة كل جديد:</b>\n"
        f"👉 <code>{TIKTOK_CHANNEL}</code>\n\n"
        "👇 <i>اضغط على زر (💡 كيف أستخدم البوت؟) بالأسفل للتعرف على الخطوات البسيطة:</i>"
    )
    inline_kb = [
        [InlineKeyboardButton("💡 اضغط هنا لطريقة الاستخدام بالتفصيل 💡", callback_data="show_help")],
        [InlineKeyboardButton("🔥 حساب صلوح المانعي على تيك توك 🔥", url=TIKTOK_CHANNEL)],
        [InlineKeyboardButton("💬 واتساب صلوح", url=WHATSAPP_URL), InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
    ]
    reply_kb = [
        [KeyboardButton("💡 كيف أستخدم البوت؟"), KeyboardButton("🔥 حساب تيك توك الرسمي")],
        [KeyboardButton("🎬 طلب فيلم سينمائي"), KeyboardButton("🎵 طلب شيلة MP3")],
        [KeyboardButton("⚽ ملخص مباريات اليوم"), KeyboardButton("💬 تواصل مع المطور صلوح")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(inline_kb), parse_mode="HTML")
    await update.message.reply_text(
        "⚡️ أزرار التحكم السريع جاهزة أسفل شاشتك في أي وقت:",
        reply_markup=ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
    await update.message.reply_text(get_help_message(), reply_markup=btn, parse_mode="HTML")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_help":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
        await query.message.reply_text(get_help_message(), reply_markup=btn, parse_mode="HTML")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المطور لمعرفة عدد الزوار والمستخدمين بالتفصيل"""
    user_id = update.effective_user.id
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        return

    users = load_users()
    total_users = len(users)
    today = time.strftime("%Y-%m-%d")
    active_today = sum(1 for u in users.values() if u.get("last_active") == today)
    joined_today = sum(1 for u in users.values() if u.get("joined_date") == today)

    report = (
        "📊 <b>إحصائيات زوار ومستخدمي البوت الحقيقية:</b>\n\n"
        f"👥 <b>إجمالي عدد المستخدمين:</b> <code>{total_users}</code> مستخدم\n"
        f"⚡️ <b>المتفاعلون اليوم:</b> <code>{active_today}</code> شخص\n"
        f"🆕 <b>المشتركون الجدد اليوم:</b> <code>{joined_today}</code> شخص\n\n"
        f"🆔 آيدي حسابك: <code>{user_id}</code>\n"
        f"👑 إدارة: <b>صلوح المانعي</b>"
    )
    await update.message.reply_text(report, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    output_base = f"downloads/{chat_id}_{msg_id}"
    os.makedirs("downloads", exist_ok=True)

    # الأزرار التفاعلية
    if text in ["💡 كيف أستخدم البوت؟", "طريقة الاستخدام", "شرح البوت"]:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
        await update.message.reply_text(get_help_message(), reply_markup=btn, parse_mode="HTML")
        return

    if text == "🔥 حساب تيك توك الرسمي":
        msg = f"🎬 <b>الحساب الرسمي لصلوح المانعي على تيك توك:</b>\n\n🔗 {TIKTOK_CHANNEL}"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ فتح حساب التيك توك مباشرة ✨", url=TIKTOK_CHANNEL)]])
        await update.message.reply_text(msg, reply_markup=btn, parse_mode="HTML")
        return

    if text == "💬 تواصل مع المطور صلوح":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 مراسلة صلوح على واتساب", url=WHATSAPP_URL)]])
        await update.message.reply_text("👑 يسعدنا تواصلك مع المطور صلوح المانعي:", reply_markup=btn)
        return

    if text == "🎬 طلب فيلم سينمائي":
        await update.message.reply_text("🎬 أرسل الآن اسم الفيلم الذي تريده مباشرة وسأجلب لك مقطعه وملخصه فوراً!")
        return

    if text == "🎵 طلب شيلة MP3":
        await update.message.reply_text("🎵 أرسل الآن اسم الشيلة أو الأغنية وسأستخرجها لك بصوت نقي MP3 فوراً!")
        return

    if text == "⚽ ملخص مباريات اليوم":
        reply = ask_super_ai("ما هي أهم قمم ومواعيد مباريات اليوم الكروية وأبرز النتائج؟")
        await update.message.reply_text(reply, parse_mode="HTML")
        return

    # 1. روابط تيك توك
    url_found = extract_url(text)
    if url_found and ("tiktok.com" in url_found.lower() or "douyin.com" in url_found.lower()):
        wait_msg = await update.message.reply_text("⚡️ <b>جاري سحب المقطع بأعلى دقة وبدون علامة مائية... ✨</b>", parse_mode="HTML")
        out_vid = f"{output_base}.mp4"
        data = download_tiktok_smart(url_found, out_vid)
        if data and os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
            caption = (
                f"🎬 <b>تفضل الفيديو بأعلى دقة وبدون علامة مائية:</b>\n\n"
                f"📌 <b>{data['title'][:100]}</b>\n\n"
                f"✨ بواسطة: <b>{BOT_NAME}</b>\n"
                f"🔥 للمزيد تابع حسابنا: <b>{TIKTOK_USER}</b>"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
            with open(out_vid, "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
            await wait_msg.delete()
            try: os.remove(out_vid)
            except Exception: pass
            return
        else:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو ليس خاصاً أو محذوفاً.")
            try: os.remove(out_vid)
            except Exception: pass
            return

    # 2. طلبات الشيلات والأغاني بصيغة MP3 صوت فوراً
    audio_keywords = ["شيله", "شيلة", "شيلات", "اغنيه", "اغنية", "أغنية", "صوت", "انشوده", "أنشودة", "زوامل", "زامل"]
    if any(k in text.lower() for k in audio_keywords):
        wait_msg = await update.message.reply_text("🎵 <b>جاري سحب الصوت بأعلى نقاوة MP3 (320kbps) فوراً... ✨</b>", parse_mode="HTML")
        clean_q = text
        for k in ["اريد", "تنزيل", "شيله", "شيلة", "اغنيه", "أغنية", "صوت", "قم بتحميل"]:
            clean_q = clean_q.replace(k, "")
        clean_q = clean_q.strip() or text

        out_audio = f"{output_base}.mp3"
        try:
            info = download_universal_media(clean_q, out_audio, is_audio=True, is_search=True)
            actual_file = out_audio if os.path.exists(out_audio) else (glob.glob(f"{output_base}.*") or [None])[0]
            
            if actual_file and os.path.exists(actual_file) and os.path.getsize(actual_file) > 1000:
                title = info.get("title", clean_q) if info else clean_q
                caption = (
                    f"🎵 <b>تم استخراج الصوت بنقاوة كاملة:</b>\n\n"
                    f"📌 <b>{title[:100]}</b>\n\n"
                    f"✨ تم بواسطة: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(actual_file, "rb") as aud:
                    await update.message.reply_audio(audio=aud, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
                try: os.remove(actual_file)
                except Exception: pass
                return
        except Exception:
            pass

    # 3. طلبات الأفلام، المسلسلات، والمقاطع الكبيرة مع القص التلقائي
    is_media_request = any(k in text.lower() for k in ["فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص"]) or bool(url_found)
    if is_media_request:
        wait_msg = await update.message.reply_text("🎬 <b>جاري سحب المقطع بأعلى دقة وفحص الحجم... ✨</b>", parse_mode="HTML")
        target = url_found if url_found else text.replace("اريد", "").replace("تنزيل", "").replace("فيلم", "").strip()
        out_raw = f"{output_base}_raw.mp4"
        out_trimmed = f"{output_base}_final.mp4"

        try:
            info = download_universal_media(target, out_raw, is_audio=False, is_search=not bool(url_found))
            actual_raw = out_raw if os.path.exists(out_raw) else (glob.glob(f"{output_base}_raw*") or [None])[0]

            if actual_raw and os.path.exists(actual_raw):
                raw_size = os.path.getsize(actual_raw)
                final_file = actual_raw
                is_trimmed = False

                if raw_size > MAX_SAFE_BYTES:
                    await wait_msg.edit_text("✂️ <b>حجم الفيديو الأصلي ضخم، جاري قص الجزء الأول بأعلى دقة (48MB)...</b>", parse_mode="HTML")
                    success = trim_video_to_size(actual_raw, out_trimmed, target_size_bytes=MAX_SAFE_BYTES)
                    if success:
                        final_file = out_trimmed
                        is_trimmed = True

                title = info.get("title", target) if info else target
                caption = (
                    f"🎬 <b>{title[:100]}</b>\n\n"
                    f"{'⚠️ تم قص الجزء الأول بأعلى جودة لمطابقة حد تيليجرام 48MB.' if is_trimmed else '✨ تم تنزيل الفيديو بأعلى جودة متوفرة.'}\n\n"
                    f"👑 بواسطة: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حساب صلوح: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(final_file, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
                
                for f in [actual_raw, out_trimmed]:
                    try: 
                        if os.path.exists(f): os.remove(f)
                    except Exception: pass
                return
        except Exception as e:
            logging.error(f"Media handler error: {e}")

    # 4. الذكاء الاصطناعي العام
    wait_msg = await update.message.reply_text("⚡️ <b>صلوح المانعي يجهز لك الإجابة الدقيقة فوراً... ✨</b>", parse_mode="HTML")
    reply = ask_super_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    threading.Thread(target=auto_clean_temp_files, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بكامل مميزات الاستخدام والإحصائيات 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
