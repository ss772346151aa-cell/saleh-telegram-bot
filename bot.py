import os
import telebot
from telebot import types
import requests
import threading
import urllib.parse
import re
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import yt_dlp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== خادم فحص الحالة لـ Render ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Saleh Mega Downloader Engine is Live 24/7!".encode('utf-8'))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== تهيئة التوكن والإعدادات ====================
raw_token = os.environ.get("BOT_TOKEN", "")
if not raw_token:
    raise ValueError("BOT_TOKEN is not set!")

BOT_TOKEN = raw_token.strip()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

# ==================== محرك السحب والتنزيل المباشر ====================
def download_media_file(url: str, chat_id: int):
    output_filename = f"video_{chat_id}_{int(time.time())}.mp4"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'geo_bypass': True,
        'socket_timeout': 30,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'مقطع فيديو')
        
        if not os.path.exists(output_filename):
            for f in os.listdir('.'):
                if f.startswith(f"video_{chat_id}"):
                    output_filename = f
                    break
        
        return output_filename, title

def fetch_tiktok_fast(url: str):
    try:
        api = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        r = requests.get(api, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}).json()
        if r.get("code") == 0:
            d = r["data"]
            v = d.get("hdplay") or d.get("play") or d.get("wmplay")
            if v.startswith("/"): v = "https://www.tikwm.com" + v
            return v, d.get("title", "فيديو تيك توك"), d.get("music")
    except Exception:
        pass
    return None, None, None

# ==================== الأزرار والواجهة ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>يدعم التحميل الفوري وبأعلى دقة من:</b>\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Facebook:</b> Reels & Videos\n"
        "• <b>YouTube:</b> Shorts & Videos\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== معالجة الروابط وشريط التقدم ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    url = url_match.group(0)

    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفك تشفير الرابط...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    if "tiktok.com" in url or "douyin.com" in url:
        v_url, title, a_url = fetch_tiktok_fast(url)
        if v_url:
            bot.edit_message_text(
                "⚡️ <b>جاري التجهيز والإرسال المباشر...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )
            key = f"tik_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = a_url or v_url

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"aud_{key}")
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )
            try:
                bot.send_video(message.chat.id, v_url, caption=caption, reply_markup=markup)
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                pass

    try:
        bot.edit_message_text(
            "⚡️ <b>جاري جلب الفيديو بأعلى دقة ومعالجة الصوت...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        file_path, video_title = download_media_file(url, message.chat.id)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            bot.edit_message_text(
                "🚀 <b>جاري رفع المقطع إلى التيليجرام...</b>\n"
                "<code>[█████████░] 90%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"loc_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = file_path

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"aud_{key}")
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            with open(file_path, 'rb') as vf:
                bot.send_video(message.chat.id, vf, caption=caption, reply_markup=markup, supports_streaming=True)

            bot.delete_message(message.chat.id, wait_msg.message_id)

            def cleanup(p):
                time.sleep(180)
                try:
                    if os.path.exists(p): os.remove(p)
                except Exception: pass
            threading.Thread(target=cleanup, args=(file_path,), daemon=True).start()
            return

    except Exception as e:
        logger.error(f"Download processing error: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== زر استخراج الصوت MP3 ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("aud_"))
def handle_audio_btn(call):
    key = call.data.replace("aud_", "")
    source = AUDIO_STORE.get(key)

    if not source:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا المقطع، يرجى إعادة إرسال الرابط.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج الصوت...")
    load = bot.send_message(call.message.chat.id, "⚡️ <b>جاري إرسال ملف الصوت MP3...</b>")

    try:
        caption = f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}"
        if source.startswith("http"):
            bot.send_audio(call.message.chat.id, source, caption=caption)
        else:
            with open(source, 'rb') as af:
                bot.send_audio(call.message.chat.id, af, caption=caption)
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل.", call.message.chat.id, load.message_id)

# ==================== الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من إنستغرام ريلز، تيك توك، أو فيسبوك وأرسله هنا مباشرة وسيتم تحميله فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو (Instagram, TikTok, Facebook, YouTube) وسأسحبه لك فوراً 🚀")

if __name__ == "__main__":
    logger.info("Bot Engine Started...")
    bot.infinity_polling(timeout=60)
