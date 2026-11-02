import os
import telebot
from telebot import types
import requests
import threading
import urllib.parse
import re
import json
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Saleh Downloader Platform is Live 24/7!".encode('utf-8'))

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

# ==================== إعدادات التوكن والهوية ====================
raw_token = os.environ.get("BOT_TOKEN", "")
if not raw_token:
    raise ValueError("BOT_TOKEN environment variable is not set!")

BOT_TOKEN = raw_token.strip()
ADMIN_ID = 7206214234
BOT_NAME = "بوت صلوح للتحميل السريع ⚡️👑"
BOT_USERNAME = "saleh_down_bot"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# مخزن مؤقت لروابط الصوت
AUDIO_CACHE = {}

# ==================== فك الروابط المختصرة التلقائي ====================
def expand_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X)'}
        res = requests.head(url, allow_redirects=True, timeout=8, headers=headers)
        return res.url
    except Exception:
        return url

# ==================== محرك جلب الميديا فائق السرعة ====================
def fetch_media(url: str):
    real_url = expand_url(url)

    # 1. تيك توك بكافة صيغه (vt, vm, tiktok.com)
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        # سيرفر 1: TikWM CDN
        try:
            clean_url = real_url.split('?')[0]
            api = f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_url)}"
            res = requests.get(api, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12).json()
            if res.get("code") == 0:
                d = res["data"]
                v_url = d.get("hdplay") or d.get("play") or d.get("wmplay")
                if v_url.startswith("/"): v_url = "https://www.tikwm.com" + v_url
                a_url = d.get("music")
                if a_url and a_url.startswith("/"): a_url = "https://www.tikwm.com" + a_url
                return {
                    "video": v_url,
                    "audio": a_url,
                    "title": d.get("title", "مقطع تيك توك")
                }
        except Exception:
            pass

        # سيرفر 2 الاحتياطي: TiklyDown
        try:
            api2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(real_url)}"
            res2 = requests.get(api2, timeout=10).json()
            v_url = res2.get("video", {}).get("noWatermark")
            a_url = res2.get("music", {}).get("play_url")
            if v_url:
                return {"video": v_url, "audio": a_url, "title": res2.get("title", "مقطع تيك توك")}
        except Exception:
            pass

    # 2. فيسبوك، إنستغرام، يوتيوب شورتس
    try:
        cobalt_api = "https://co.wuk.sh/api/json"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {"url": real_url, "vQuality": "720"}
        res3 = requests.post(cobalt_api, json=payload, headers=headers, timeout=12).json()
        if res3.get("url"):
            return {
                "video": res3["url"],
                "audio": res3["url"],
                "title": "مقطع فيديو"
            }
    except Exception:
        pass

    # سيرفر VKR الشامل
    try:
        vkr = f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(real_url)}"
        r = requests.get(vkr, timeout=12).json()
        if r.get("status") == "success" and "data" in r:
            return {
                "video": r["data"].get("hd") or r["data"].get("sd"),
                "audio": None,
                "title": r["data"].get("title", "فيديو")
            }
    except Exception:
        pass

    return None

# ==================== واجهة البوت ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت التحميل السريع!</b>\n\n"
        "⚡️ أرسل أي رابط من:\n"
        "• <b>تيك توك</b> (TikTok)\n"
        "• <b>إنستغرام</b> (Reels / Posts)\n"
        "• <b>فيسبوك</b> (Reels / Videos)\n"
        "• <b>يوتيوب</b> (Shorts / Video)\n\n"
        "🚀 وسأرسل لك الفيديو مباشرة بأعلى دقة وبدون علامة مائية مع خيار استخراج الصوت MP3!"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_keyboard())

# ==================== معالجة الروابط وتحديث العداد ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    url = url_match.group(0)

    # إرسال رسالة المعالجة الأولية
    wait_msg = bot.reply_to(message, "⏳ <b>جاري الاتصال بالسيرفر وجلب الفيديو...</b>\n[░░░░░░░░░░] 10%")

    try:
        # محاكاة سريعة للعداد أثناء الفحص المباشر
        time.sleep(0.4)
        bot.edit_message_text("⚡️ <b>جاري فك التشفير وتجهيز أعلى دقة...</b>\n[█████░░░░░] 50%", message.chat.id, wait_msg.message_id)
        
        data = fetch_media(url)

        if data and data.get("video"):
            bot.edit_message_text("🚀 <b>جاري رفع المقطع إليك الآن...</b>\n[██████████] 100%", message.chat.id, wait_msg.message_id)
            
            # تخزين رابط الصوت لاستخراجه عند الطلب
            key = f"media_{message.chat.id}_{int(time.time())}"
            AUDIO_CACHE[key] = data.get("audio") or data.get("video")

            # لوحة الأزرار الشبيهة بنسخة البوت الاحترافي في الصورة
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"audio_{key}")
            
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            bot.send_video(message.chat.id, data["video"], caption=caption, reply_markup=markup)
            bot.delete_message(message.chat.id, wait_msg.message_id)
            return

    except Exception as e:
        logger.error(f"Download Error: {e}")

    bot.edit_message_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو عام وغير محذوف.", message.chat.id, wait_msg.message_id)

# ==================== زر استخراج الصوت MP3 ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("audio_"))
def handle_audio_extract(call):
    key = call.data.replace("audio_", "")
    audio_url = AUDIO_CACHE.get(key)

    if not audio_url:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا المقطع، يرجى إعادة إرسال الرابط.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج الصوت MP3...")
    wait = bot.send_message(call.message.chat.id, "⚡️ <b>جاري تجهيز ملف MP3...</b>")
    try:
        bot.send_audio(call.message.chat.id, audio_url, caption=f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}")
        bot.delete_message(call.message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر استخراج الصوت مباشرة من هذا المصدر.", call.message.chat.id, wait.message_id)

# ==================== الرسائل النصية ====================
@bot.message_handler(func=lambda m: True)
def default_reply(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من تيك توك، إنستغرام، أو فيسبوك وأرسله هنا مباشرة في المحادثة!")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو الذي تريد تحميله وسأجلبه لك فوراً 🚀")

if __name__ == "__main__":
    logger.info("Bot is polling...")
    bot.infinity_polling(timeout=60)
