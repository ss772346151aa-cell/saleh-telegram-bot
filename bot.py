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
        return  # إسكات السجلات للحفاظ على نظافة الـ Console
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Mega Engine is Live 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. إعدادات التوكن والهوية ====================
# التوكن الجديد المخصص للبوت
DEFAULT_TOKEN = "9157081412:AAFNd58PvaVueVhHeWB_b0AWheOYDUi2_zE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN).strip()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

# ==================== 3. محرك فك الروابط واستخراج الوسائط المباشرة ====================
def resolve_short_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.head(url, allow_redirects=True, timeout=8, headers=headers)
        return res.url
    except Exception:
        return url

def fetch_stream_data(raw_url: str):
    clean_url = resolve_short_url(raw_url)

    # 1. تيك توك بكافة أشكاله (vt.tiktok, vm, tiktok.com)
    if "tiktok.com" in clean_url or "douyin.com" in clean_url:
        try:
            api = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(clean_url)}"
            r = requests.get(api, timeout=10).json()
            v_url = r.get("video", {}).get("noWatermark")
            a_url = r.get("music", {}).get("play_url")
            if v_url:
                return {"video": v_url, "audio": a_url, "title": r.get("title", "فيديو تيك توك")}
        except Exception:
            pass

        try:
            api2 = f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_url.split('?')[0])}"
            r2 = requests.get(api2, timeout=10).json()
            if r2.get("code") == 0:
                d = r2["data"]
                v_url = d.get("hdplay") or d.get("play") or d.get("wmplay")
                if v_url.startswith("/"): v_url = "https://www.tikwm.com" + v_url
                a_url = d.get("music")
                if a_url and a_url.startswith("/"): a_url = "https://www.tikwm.com" + a_url
                return {"video": v_url, "audio": a_url, "title": d.get("title", "فيديو تيك توك")}
        except Exception:
            pass

    # 2. إنستغرام وفيسبوك وبقية المنصات (استخراج CDN مباشر لتجاوز حد 50MB)
    gateways = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt.api.scidsg.org/api/json",
        "https://co.wuk.sh/api/json"
    ]
    for gate in gateways:
        try:
            payload = {"url": clean_url, "vQuality": "720"}
            res = requests.post(gate, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=8).json()
            if res.get("url"):
                return {"video": res["url"], "audio": res["url"], "title": "مقطع فيديو"}
        except Exception:
            continue

    # محرك احتياطي مباشر لإنستغرام
    try:
        if "instagram.com" in clean_url:
            r = requests.get(f"https://api.vkrdownloader.com/instagram/video.php?url={urllib.parse.quote(clean_url)}", timeout=10).json()
            if r.get("status") == "success" and "data" in r:
                v = r["data"].get("url") or r["data"].get("video_url")
                if v: return {"video": v, "audio": v, "title": "إنستغرام ريلز"}
    except Exception:
        pass

    # محرك احتياطي مباشر لفيسبوك
    try:
        if "facebook.com" in clean_url or "fb.watch" in clean_url:
            r = requests.get(f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(clean_url)}", timeout=10).json()
            if r.get("status") == "success" and "data" in r:
                v = r["data"].get("hd") or r["data"].get("sd")
                if v: return {"video": v, "audio": v, "title": "فيسبوك فيديو"}
    except Exception:
        pass

    return None

# ==================== 4. الواجهة والأزرار ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>يدعم التحميل الفوري وبأعلى دقة متجاوزاً أي حدود للحجم من:</b>\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Facebook:</b> Reels & Videos\n"
        "• <b>YouTube:</b> Shorts & Videos\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== 5. معالجة الروابط وشريط العداد الفوري ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download(message):
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
            "⚡️ <b>جاري تجهيز البث المباشر بأعلى دقة وتخطي حد 50MB...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        data = fetch_stream_data(raw_url)

        if data and data.get("video"):
            bot.edit_message_text(
                "🚀 <b>تم التجهيز، جاري تسليم المقطع لشاشتك...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = data.get("audio") or data.get("video")

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

            try:
                bot.send_video(
                    message.chat.id, 
                    data["video"], 
                    caption=caption, 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                stream = requests.get(data["video"], stream=True, timeout=20)
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
        logger.error(f"Download Error: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 6. استخراج الصوت MP3 ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ext_"))
def handle_audio(call):
    key = call.data.replace("ext_", "")
    source = AUDIO_STORE.get(key)

    if not source:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط، أعد إرسال الفيديو.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج الصوت...")
    load = bot.send_message(call.message.chat.id, "⚡️ <b>جاري إرسال ملف الصوت MP3...</b>")
    try:
        bot.send_audio(call.message.chat.id, source, caption=f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}")
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== 7. الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من إنستغرام، تيك توك، أو فيسبوك وأرسله هنا وسأسحبه لك فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو (Instagram, TikTok, Facebook, YouTube) وسأسحبه لك فوراً 🚀")

# ==================== 8. حلقة التشغيل ومعالجة تعارض 409 ====================
if __name__ == "__main__":
    logger.info("Starting Saleh Mega Engine...")
    
    # تفريغ أي اتصال قديم أو Webhook عالق
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Webhook reset: {e}")

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=25)
        except telebot.apihelper.ApiTelegramException as api_err:
            if api_err.error_code == 409:
                logger.error("Conflict 409 detected. Waiting 10s...")
                time.sleep(10)
            else:
                logger.error(f"API Error: {api_err}")
                time.sleep(3)
        except Exception as err:
            logger.error(f"Unexpected crash, restarting in 5s: {err}")
            time.sleep(5)
