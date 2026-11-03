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
        self.wfile.write(b"Saleh Mega Engine is Live 24/7!")

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

# ==================== 2. تهيئة التوكن والإعدادات ====================
DEFAULT_TOKEN = "9157081412:AAFNd58PvaVueVhHeWB_b0AWheOYDUi2_zE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN).strip()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

# ==================== 3. محرك فك الروابط التلقائي ====================
def unshorten_url(url: str) -> str:
    """فك روابط vt.tiktok و fb.watch و threads وغيرها"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        }
        res = requests.head(url, allow_redirects=True, timeout=8, headers=headers)
        return res.url
    except Exception:
        try:
            res = requests.get(url, allow_redirects=True, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            return res.url
        except Exception:
            return url

# ==================== 4. شبكة المحركات العالمية (Multi-Node Engine) ====================
def extract_media(raw_url: str):
    real_url = unshorten_url(raw_url)
    clean_url = real_url.split('?')[0]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': '*/*'
    }

    # ------------------ أ) محركات TikTok المتقدمة ------------------
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        # المحرك 1: TikWM Raw API
        try:
            api1 = f"https://www.tikwm.com/api/?url={urllib.parse.quote(real_url)}"
            r1 = requests.get(api1, headers=headers, timeout=8).json()
            if r1.get("code") == 0:
                data = r1["data"]
                v = data.get("hdplay") or data.get("play") or data.get("wmplay")
                if v and v.startswith("/"): v = "https://www.tikwm.com" + v
                a = data.get("music")
                if a and a.startswith("/"): a = "https://www.tikwm.com" + a
                if v: return {"video": v, "audio": a or v, "title": data.get("title", "فيديو تيك توك")}
        except Exception:
            pass

        # المحرك 2: TiklyDown Node
        try:
            api2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(clean_url)}"
            r2 = requests.get(api2, headers=headers, timeout=8).json()
            if r2.get("video", {}).get("noWatermark"):
                return {
                    "video": r2["video"]["noWatermark"],
                    "audio": r2.get("music", {}).get("play_url"),
                    "title": r2.get("title", "فيديو تيك توك")
                }
        except Exception:
            pass

        # المحرك 3: LoveTik Node
        try:
            r3 = requests.post("https://lovetik.com/api/ajax/search", data={"query": real_url}, headers=headers, timeout=8).json()
            if r3.get("links") and len(r3["links"]) > 0:
                v = r3["links"][0].get("a")
                a = r3["links"][-1].get("a")
                if v: return {"video": v, "audio": a or v, "title": r3.get("desc", "فيديو تيك توك")}
        except Exception:
            pass

    # ------------------ ب) محركات Instagram & Threads ------------------
    if "instagram.com" in real_url or "threads.com" in real_url or "threads.net" in real_url:
        # المحرك 1: FastDL Gateway
        try:
            r_ig1 = requests.post("https://fastdl.app/c/", json={"url": real_url}, headers=headers, timeout=10).json()
            if r_ig1.get("items") and len(r_ig1["items"]) > 0:
                item = r_ig1["items"][0]
                v = item.get("urls", [{}])[0].get("url")
                if v: return {"video": v, "audio": v, "title": "ريلز إنستغرام"}
        except Exception:
            pass

        # المحرك 2: SnapInsta Gateway
        try:
            r_ig2 = requests.post("https://api.snapinsta.to/api/ajaxSearch", data={"q": real_url, "t": "media", "lang": "en"}, headers=headers, timeout=10).json()
            if "data" in r_ig2:
                match = re.search(r'href="([^"]+)" download', r_ig2["data"])
                if match: return {"video": match.group(1), "audio": match.group(1), "title": "ريلز إنستغرام"}
        except Exception:
            pass

        # المحرك 3: SaveInsta Gateway
        try:
            r_ig3 = requests.post("https://saveinsta.app/api/ajaxSearch", data={"q": real_url, "t": "media", "lang": "en"}, headers=headers, timeout=10).json()
            if "data" in r_ig3:
                m = re.search(r'href="([^"]+)"[^>]*class="btn\s*btn-download', r_ig3["data"])
                if m: return {"video": m.group(1), "audio": m.group(1), "title": "إنستغرام فيديو"}
        except Exception:
            pass

    # ------------------ ج) محركات Facebook ------------------
    if "facebook.com" in real_url or "fb.watch" in real_url:
        try:
            r_fb = requests.post("https://fdownloader.net/api/ajaxSearch", data={"k_exp": "", "k_token": "", "q": real_url, "lang": "en"}, headers=headers, timeout=10).json()
            if "data" in r_fb:
                m = re.search(r'href="(https://[^"]+)"\s*class="btn\s*btn-download', r_fb["data"])
                if m: return {"video": m.group(1), "audio": m.group(1), "title": "فيديو فيسبوك"}
        except Exception:
            pass

    # ------------------ د) البوابات السحابية الشاملة (Cobalt Global Nodes) ------------------
    cobalt_nodes = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt.api.scidsg.org/api/json",
        "https://co.wuk.sh/api/json"
    ]
    for c_node in cobalt_nodes:
        try:
            payload = {"url": real_url, "vQuality": "720"}
            r_c = requests.post(c_node, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=8).json()
            if r_c.get("url"):
                return {"video": r_c["url"], "audio": r_c["url"], "title": "مقطع فيديو"}
        except Exception:
            continue

    return None

# ==================== 5. لوحة المفاتيح والترحيب ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>يدعم التحميل الفوري وبأعلى دقة متجاوزاً أي حدود للحجم من:</b>\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>Threads:</b> الفيديوهات والصور\n"
        "• <b>Facebook:</b> Reels & Videos\n"
        "• <b>YouTube:</b> Shorts & Videos\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== 6. معالجة الروابط وعرض العداد التفاعلي ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download_request(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    # المرحلة 1: شريط العداد (20%)
    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفك تشفير الرابط...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        # المرحلة 2: محاكاة فك التشفير وتجهيز البث (60%)
        time.sleep(0.3)
        bot.edit_message_text(
            "⚡️ <b>جاري فحص البوابات السحابية وتجاوز حد 50MB...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        media = extract_media(raw_url)

        if media and media.get("video"):
            # المرحلة 3: اكتمال المعالجة (100%)
            bot.edit_message_text(
                "🚀 <b>تم التجهيز بنجاح! جاري إرسال المقطع لشاشتك...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = media.get("audio") or media.get("video")

            # الأزرار الاحترافية المطابقة تماماً للصورة
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

            # محاولة الإرسال السريع كـ Direct Stream URL (تجاوز 50MB)
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
                # إذا تطلب الأمر سحب متدفق كـ Raw Stream
                headers = {'User-Agent': 'Mozilla/5.0'}
                stream = requests.get(media["video"], headers=headers, stream=True, timeout=30)
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
        logger.error(f"Download Engine Failed: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 7. استخراج الصوت MP3 ====================
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

# ==================== 8. الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من تيك توك، إنستغرام، ثريدز، أو فيسبوك وأرسله هنا وسأسحبه لك فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو (TikTok, Instagram, Threads, Facebook) وسأسحبه لك فوراً 🚀")

# ==================== 9. حلقة التشغيل الآمنة ====================
if __name__ == "__main__":
    logger.info("Multi-Node Mega Engine Started...")
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
