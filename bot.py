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

# ==================== خادم فحص الحالة السحابي (Render 24/7) ====================
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
    raise ValueError("BOT_TOKEN is not set in Environment Variables!")

BOT_TOKEN = raw_token.strip()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

# ==================== محرك فك الروابط المختصرة الذكي ====================
def get_original_url(short_url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(short_url, headers=headers, allow_redirects=True, timeout=8)
        return response.url
    except Exception:
        return short_url

# ==================== مصفوفة بوابات التحميل متعددة المسارات ====================
def extract_video_data(target_url: str):
    real_url = get_original_url(target_url)
    clean_url = real_url.split('?')[0] if ("tiktok.com" in real_url or "instagram.com" in real_url) else real_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    # 1. مسار تيك توك فائق الاستقرار
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        # المحاولة عبر بوابة TiklyDown العالمية المفتوحة
        try:
            r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(real_url)}", headers=headers, timeout=10).json()
            if "video" in r and r["video"].get("noWatermark"):
                return {
                    "video": r["video"]["noWatermark"],
                    "audio": r.get("music", {}).get("play_url"),
                    "title": r.get("title", "فيديو تيك توك")
                }
        except Exception:
            pass

        # المحاولة عبر بوابة TikWM بصيغة الجوال المباشرة
        try:
            r2 = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_url)}", headers=headers, timeout=10).json()
            if r2.get("code") == 0:
                d = r2["data"]
                v = d.get("hdplay") or d.get("play") or d.get("wmplay")
                if v.startswith("/"): v = "https://www.tikwm.com" + v
                a = d.get("music")
                if a and a.startswith("/"): a = "https://www.tikwm.com" + a
                return {"video": v, "audio": a, "title": d.get("title", "فيديو تيك توك")}
        except Exception:
            pass

    # 2. مسار إنستغرام وفيسبوك وبقية المنصات عبر بوابات الـ CDN المفتوحة
    api_nodes = [
        "https://api.cobalt.tools/api/json",
        "https://co.wuk.sh/api/json",
        "https://cobalt.api.scidsg.org/api/json"
    ]

    for node in api_nodes:
        try:
            payload = {"url": real_url, "vQuality": "720"}
            r = requests.post(node, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=8).json()
            if r.get("url"):
                return {"video": r["url"], "audio": r.get("url"), "title": "مقطع فيديو"}
        except Exception:
            continue

    # 3. البوابة الاحتياطية المباشرة لإنستغرام وفيسبوك
    try:
        if "instagram.com" in real_url:
            r = requests.get(f"https://api.vkrdownloader.com/instagram/video.php?url={urllib.parse.quote(real_url)}", headers=headers, timeout=10).json()
            if r.get("status") == "success" and "data" in r:
                v = r["data"].get("url") or r["data"].get("video_url")
                if v: return {"video": v, "audio": v, "title": "إنستغرام ريلز"}
    except Exception:
        pass

    try:
        if "facebook.com" in real_url or "fb.watch" in real_url:
            r = requests.get(f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(real_url)}", headers=headers, timeout=10).json()
            if r.get("status") == "success" and "data" in r:
                v = r["data"].get("hd") or r["data"].get("sd")
                if v: return {"video": v, "audio": v, "title": "فيسبوك فيديو"}
    except Exception:
        pass

    return None

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
def handle_download_request(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    url = url_match.group(0)

    # 1. المرحلة الأولى: الاتصال
    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفك تشفير الرابط...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        # 2. المرحلة الثانية: استخراج البيانات
        media_data = extract_video_data(url)

        if media_data and media_data.get("video"):
            bot.edit_message_text(
                "⚡️ <b>تم جلب المقطع بأعلى دقة، جاري الإرسال المباشر...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"med_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = media_data.get("audio") or media_data.get("video")

            # الأزرار الاحترافية المطابقة للبوت العالمي
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

            # إرسال تيار الفيديو مباشرة بدون ضغط على السيرفر
            try:
                bot.send_video(
                    message.chat.id, 
                    media_data["video"], 
                    caption=caption, 
                    reply_markup=markup,
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                # إذا تطلب الأمر سحب مباشر كـ Stream خام
                stream_res = requests.get(media_data["video"], stream=True, timeout=20)
                bot.send_video(
                    message.chat.id, 
                    stream_res.raw, 
                    caption=caption, 
                    reply_markup=markup,
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return

    except Exception as e:
        logger.error(f"Download Error: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== استخراج الصوت MP3 ====================
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
        bot.send_audio(call.message.chat.id, source, caption=caption)
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من إنستغرام ريلز، تيك توك، أو فيسبوك وأرسله هنا مباشرة وسيتم سحبه فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو (Instagram, TikTok, Facebook, YouTube) وسأسحبه لك فوراً 🚀")

if __name__ == "__main__":
    logger.info("Bot Engine Started...")
    bot.infinity_polling(timeout=60)
