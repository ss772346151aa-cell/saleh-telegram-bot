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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 1. خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Engine is Live 24/7!")

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
        logger.error(f"Health Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. الإعدادات والتوكن ====================
DEFAULT_TOKEN = "9157081412:AAFNd58PvaVueVhHeWB_b0AWheOYDUi2_zE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN).strip()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

RAPIDAPI_KEY = "2bbc6b508amshf8ae4c3acc0945ap121032jsn8dc7afbfa9bc"
RAPIDAPI_HOST = "instagram-tiktok-youtube-downloader.p.rapidapi.com"

# ==================== 3. محرك الاستخراج الدقيق للـ API ====================
def extract_media_from_api(url: str):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    # 1. الاستعلام عبر المسار الرئيسي
    endpoints = [
        f"https://{RAPIDAPI_HOST}/",
        f"https://{RAPIDAPI_HOST}/download",
        f"https://{RAPIDAPI_HOST}/media"
    ]
    
    for ep in endpoints:
        try:
            res = requests.get(ep, headers=headers, params={"url": url}, timeout=15)
            logger.info(f"API {ep} -> Status: {res.status_code}")
            if res.status_code == 200:
                data = res.json()
                logger.info(f"API Data: {data}")

                video = (
                    data.get("download_url") or 
                    data.get("url") or 
                    data.get("media") or 
                    data.get("video_url")
                )
                
                # التعامل مع منشورات الألبومات والمقاطع المتعددة
                if not video and isinstance(data.get("items"), list) and len(data["items"]) > 0:
                    first = data["items"][0]
                    video = first.get("download_url") or first.get("url") or first.get("media")

                audio = data.get("music_url") or data.get("audio") or video

                if video:
                    return {"video": video, "audio": audio}
        except Exception as e:
            logger.error(f"Error querying {ep}: {e}")

    # محرك احتياطي سريع في حال تأخر الاستجابة
    if "tiktok.com" in url:
        try:
            r = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}", timeout=10).json()
            if r.get("code") == 0:
                v = r["data"].get("hdplay") or r["data"].get("play")
                if v and v.startswith("/"): v = "https://www.tikwm.com" + v
                a = r["data"].get("music")
                if a and a.startswith("/"): a = "https://www.tikwm.com" + a
                return {"video": v, "audio": a or v}
        except Exception:
            pass

    return None

# ==================== 4. الأزرار والواجهة ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>يدعم التحميل الفوري وبأعلى دقة:</b>\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>Threads & Facebook & YouTube</b>\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== 5. معالجة الروابط وشريط العداد ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download_request(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفك تشفير الرابط...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        time.sleep(0.3)
        bot.edit_message_text(
            "⚡️ <b>جاري فحص البوابات السحابية وتجهيز البث...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        media = extract_media_from_api(raw_url)

        if media and media.get("video"):
            bot.edit_message_text(
                "🚀 <b>تم التجهيز بنجاح! جاري إرسال المقطع لشاشتك...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = media.get("audio") or media.get("video")

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"ext_{key}")
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            # محاولة إرسال الرابط المباشر
            try:
                bot.send_video(
                    message.chat.id, 
                    media["video"], 
                    caption=caption, 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                stream = requests.get(media["video"], headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                bot.send_video(
                    message.chat.id, 
                    stream.raw, 
                    caption=caption, 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return

    except Exception as e:
        logger.error(f"Download processing failed: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 6. استخراج الصوت MP3 ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ext_"))
def handle_audio_btn(call):
    key = call.data.replace("ext_", "")
    source = AUDIO_STORE.get(key)

    if not source:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط، أعد إرسال الفيديو.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج الصوت...")
    load = bot.send_message(call.message.chat.id, "⚡️ <b>جاري إرسال ملف الصوت MP3...</b>")
    try:
        caption = f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}"
        bot.send_audio(call.message.chat.id, source, caption=caption)
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== 7. الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من تيك توك، إنستغرام، ثريدز، أو فيسبوك وأرسله هنا وسأسحبه لك فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو وسأسحبه لك فوراً 🚀")

# ==================== 8. حلقة التشغيل ====================
if __name__ == "__main__":
    logger.info("Bot Engine Starting with Active RapidAPI...")
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=25)
        except telebot.apihelper.ApiTelegramException as api_err:
            if api_err.error_code == 409:
                time.sleep(10)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(5)
